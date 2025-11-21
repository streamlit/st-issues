from __future__ import annotations

from datetime import date, timedelta

import humanize
import streamlit as st

from app.utils.ai.agent_dialog import show_agent_prompt_dialog
from app.utils.github_utils import (
    get_all_github_issues,
    get_all_github_prs,
    parse_github_url,
    validate_issue_number,
    EXPECTED_FLAKY_TESTS,
)
from app.utils.interrupt_data import (
    get_community_prs_ready_for_review,
    get_confirmed_bugs_without_repro_script,
    get_flaky_tests,
    get_frontend_test_coverage_metrics,
    get_issue_waiting_for_team_response,
    get_missing_labels_issues,
    get_missing_labels_prs,
    get_needs_triage_issues,
    get_open_dependabot_prs,
    get_p0_p1_bugs,
    get_prs_needing_product_approval,
    get_python_test_coverage_metrics,
    get_unprioritized_bugs,
    get_wheel_size_metrics,
    get_bundle_size_metrics,
)

# Set page configuration
st.set_page_config(page_title="Interrupt Rotation - Dashboard", page_icon="🩺", layout="wide")

# Main app
st.title("🩺 Interrupt Rotation - Dashboard")
st.caption(
    "This dashboard provides an overview of repository health and areas that require attention."
)

timeframe = st.sidebar.selectbox(
    "Select timeframe",
    ("Last 7 days", "Last 14 days"),
    index=0,
)
if st.sidebar.button(":material/refresh: Refresh data", use_container_width=True):
    # Refresh issue and PR data:
    get_all_github_issues.clear()
    get_all_github_prs.clear()

# Agent Prompt Generation Section
st.sidebar.divider()
st.sidebar.subheader(":computer: Agent Prompt Generator")

# Manual issue number input with form
with st.sidebar.form("issue_form"):
    # URL input for auto-parsing
    github_url = st.text_input(
        "GitHub Issue URL (optional)",
        placeholder="https://github.com/owner/repo/issues/123",
        help="Paste a GitHub issue URL to auto-populate the fields below",
    )

    # Parse URL if provided
    parsed_repo, parsed_issue = parse_github_url(github_url)

    # Use parsed values as defaults if available
    default_repo = parsed_repo if parsed_repo else "streamlit/streamlit"
    default_issue = parsed_issue if parsed_issue else ""

    repo_info = st.text_input(
        "Repository (owner/repo)",
        value=default_repo,
        help="Repository in the format 'owner/repo'",
    )

    manual_issue_number = st.text_input(
        "Issue Number",
        value=default_issue,
        placeholder="e.g. 12345",
        help="Enter a GitHub issue number to generate an agent prompt",
    )

    submitted = st.form_submit_button("Open Dialog", use_container_width=True)

if submitted and manual_issue_number:
    # Validate issue number
    is_valid, validated_issue = validate_issue_number(manual_issue_number)

    if not is_valid:
        if not manual_issue_number.strip():
            st.sidebar.error("❌ Please enter an issue number.")
        else:
            st.sidebar.error(
                "❌ Issue number must be a valid number between 1 and 150,000."
            )
    elif not repo_info.strip():
        st.sidebar.error("❌ Please enter a repository in the format 'owner/repo'.")
    else:
        st.session_state.selected_issue_number = validated_issue
        st.session_state.selected_repo = repo_info
        st.session_state.selected_issue_url = (
            f"https://github.com/{repo_info}/issues/{validated_issue}"
        )
        st.session_state.show_agent_dialog = True

days = 14 if timeframe == "Last 14 days" else 7
since = date.today() - timedelta(days=days)

col1, col2, col3 = st.columns(3)
with col1:
    py_coverage, py_coverage_change = get_python_test_coverage_metrics(since)
    st.metric(
        "Python Test Coverage",
        f"{py_coverage:.2f}%",
        f"{py_coverage_change:+.2f}%",
        delta_color="normal",
        border=True,
        help="Percentage of lines covered by tests in the Python codebase.",
    )
with col2:
    fe_coverage, fe_coverage_change = get_frontend_test_coverage_metrics(since)
    st.metric(
        "Frontend Test Coverage",
        f"{fe_coverage:.2f}%",
        f"{fe_coverage_change:+.2f}%",
        delta_color="normal",
        border=True,
        help="Percentage of lines covered by tests in the Frontend codebase.",
    )
with col3:
    wheel_size, wheel_size_change = get_wheel_size_metrics(since)
    st.metric(
        "Wheel Size",
        humanize.naturalsize(wheel_size, binary=True),
        humanize.naturalsize(wheel_size_change, binary=True),
        delta_color="inverse",
        border=True,
        help="Size of the Streamlit Python package (wheel file).",
    )

col1, col2, col3 = st.columns(3)
with col1:
    (
        total_gzip,
        total_gzip_change,
        entry_gzip,
        entry_gzip_change,
    ) = get_bundle_size_metrics(since)

    st.metric(
        "Total Bundle (gzip)",
        humanize.naturalsize(total_gzip, binary=True),
        humanize.naturalsize(total_gzip_change, binary=True),
        delta_color="inverse",
        border=True,
        help="Total size of all JavaScript files after Gzip compression.",
    )
with col2:
    st.metric(
        "Entry Bundle (gzip)",
        humanize.naturalsize(entry_gzip, binary=True),
        humanize.naturalsize(entry_gzip_change, binary=True),
        delta_color="inverse",
        border=True,
        help="Size of the entry point chunks (initial load) after Gzip compression.",
    )

with st.expander("**🔄 Helpful Processes**"):
    st.markdown("""
    - [Issues on Community Cloud](https://www.notion.so/snowflake-corp/Streamlit-OS-Issues-Community-Cloud-dfa2c315cafd434081166f33077c3eb2)
    - [Evaluating Memory Leaks in Streamlit](https://www.notion.so/snowflake-corp/Evaluating-Memory-Leaks-in-Streamlit-2af7170bb41680ed8634dbd5ee414f57)
    """)

# DataFrames
st.header("Action Items")

st.subheader(
    "Issues that need triage",
    help="""
Lists all issues with the `status:needs-triage` label.
To triage an issue, you need to try to reproduce the issue.

**If you are able to reproduce the issue:**
1. Add the `status:confirmed` label
2. Remove the `status:needs-triage` label
3. Add the correct priority label `priority:P{0,1,2,3,4}`
    1. **Important:** If it's a P0 bug, you should either start working on a fix or engaging with the people who can help take immediate action on the bug
    2. If it's a P1 or P2 bug, consider prioritizing fixing the bug yourself as that is a core responsibility of the Interrupt rotation
4. Add the corresponding feature(s) label `feature:{the_feature}` or `area:{the_area}`
5. If it's a regression, add the `type:regression` label
6. If this is a bug in an upstream library (eg: Base Web, Arrow), please add the `upstream` label
7. Respond in a comment thanking the user for filing their issue

**If you are unable to repro / they didn't provide enough information to debug:**
1. Add the `status:cannot-reproduce` and `status:awaiting-user-response` labels
2. Remove the `status:needs-triage` label
3. Respond in a comment thanking the user for filing their issue and asking them for more information on how to reproduce the issue. Be clear about what you tried and what results you were seeing.

**If it is not a bug, but intended behavior:**
1. Change to the type (e.g. to `type:enhancement` , or `type:docs`, …)
2. Remove the `status:needs-triage` label
3. Respond in a comment thanking the user for filing their issue, let them know that it is intended behavior, and close the issue.
""",
)
needs_triage_df = get_needs_triage_issues()
if needs_triage_df.empty:
    st.success("Congrats, everything is done here!", icon="🎉")
else:
    st.dataframe(
        needs_triage_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Title": st.column_config.TextColumn("Title", width="large"),
            "URL": st.column_config.LinkColumn("URL", display_text="Open"),
            "Created": st.column_config.DatetimeColumn("Created", format="distance"),
            "Author": st.column_config.TextColumn("Author"),
        },
    )
st.divider()

st.subheader(
    "Issues missing feature label",
    help="Every issue is expected to have atleast one `feature:{the_feature}` or `area:{the_area}` label.",
)
missing_labels_df = get_missing_labels_issues()
if missing_labels_df.empty:
    st.success("Congrats, everything is done here!", icon="🎉")
else:
    st.dataframe(
        missing_labels_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Title": st.column_config.TextColumn("Title", width="large"),
            "URL": st.column_config.LinkColumn("URL", display_text="Open"),
            "Created": st.column_config.DatetimeColumn("Created", format="distance"),
            "Author": st.column_config.TextColumn("Author"),
            "Labels": st.column_config.ListColumn("Labels"),
        },
    )
st.divider()

st.subheader(
    "Confirmed bugs without a priority",
    help="""
Every confirmed bug is expected to be labled with a `priority:P{0,1,2,3,4}` label.

### P0

- A primary Streamlit user journey is effectively broken for nearly all users
- A high-risk security or compliance issue, even if not immediately user-visible

**Action:** Must be addressed ASAP with a hotfix

### P1

- Streamlit behavior blocks most users from doing something *without* a workaround
- A new or high profile feature is visibly broken in a common scenario
- Streamlit behavior causes a Major incident with an internal hosting partner (Community Cloud or SiS)
- A non-blocking but noticeable regression (>5% of users will notice) in a primary user journey or Streamlit behavior including:
    - Performance regression
    - Visual or design issue
    - Behavior change which breaks backwards compatibility

**Action:** If found pre-release, we will not release. If found after release, we should fix within 2 weeks and will assess a hotfix.

### P2

- Streamlit behavior blocks many users from doing something — but there is a workaround
- Something is visibly broken in an `experimental_` feature
- Streamlit behavior blocks many users from doing something specifically with a key dependency.
- A less noticeable regression (visual/design or performance) or confusing behavior

**Action:** If it's a regression and/or has a straightforward and low-risk fix, we should try to fix it in the next release. Otherwise, assess case by case.

### P3/P4

- Streamlit blocks users in specific situations (e.g. use of an outside dependency)
- Small stylistic changes
- Scenarios that have very specific situations and are difficult to reproduce.

*Distinguishing P3/P4 is more of a judgment call. Upvotes/comments in Github can also distinguish these, or even indicate visibility to move to P2.*

**Action:** It can be fixed opportunistically but should not be especially prioritized by core engineers. We may also accept an outside contribution, or fix it as a papercut.
""",
)
unprioritized_bugs_df = get_unprioritized_bugs()
if unprioritized_bugs_df.empty:
    st.success("Congrats, everything is done here!", icon="🎉")
else:
    st.dataframe(
        unprioritized_bugs_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Title": st.column_config.TextColumn("Title", width="large"),
            "URL": st.column_config.LinkColumn("URL", display_text="Open"),
            "Created": st.column_config.DatetimeColumn("Created", format="distance"),
            "Author": st.column_config.TextColumn("Author"),
        },
    )
st.divider()

st.subheader(
    "P0 and P1 Bugs",
    help="""
Lists high-priority bugs that require immediate attention.
Please make sure that those bugs are assigned and are being worked on.
""",
)
p0_p1_bugs_df = get_p0_p1_bugs()
if p0_p1_bugs_df.empty:
    st.success("Congrats, everything is done here!", icon="🎉")
else:
    # Sort by priority (P0 first, then P1) and then by creation date
    p0_p1_bugs_df["Priority_Sort"] = p0_p1_bugs_df["Priority"].map(
        {"priority:P0": 0, "priority:P1": 1}
    )
    p0_p1_bugs_df = p0_p1_bugs_df.sort_values(by=["Priority_Sort", "Created"])
    p0_p1_bugs_df = p0_p1_bugs_df.drop("Priority_Sort", axis=1)

    st.dataframe(
        p0_p1_bugs_df.drop("Priority_Sort", axis=1, errors="ignore"),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Title": st.column_config.TextColumn("Title", width="large"),
            "URL": st.column_config.LinkColumn("URL", display_text="Open"),
            "Created": st.column_config.DatetimeColumn("Created", format="distance"),
            "Author": st.column_config.TextColumn("Author"),
            "Priority": st.column_config.TextColumn("Priority"),
            "Assignees": st.column_config.ListColumn("Assignees"),
        },
    )
st.divider()

st.subheader(
    "Community PRs missing labels",
    help="Every community PR is expected to be labeled with a `change:*` and `impact:*` label.",
)
missing_labels_prs_df = get_missing_labels_prs()
if missing_labels_prs_df.empty:
    st.success("Congrats, everything is done here!", icon="🎉")
else:
    st.dataframe(
        missing_labels_prs_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Title": st.column_config.TextColumn("Title", width="large"),
            "URL": st.column_config.LinkColumn("URL", display_text="Open"),
            "Created": st.column_config.DatetimeColumn("Created", format="distance"),
            "Labels": st.column_config.ListColumn("Labels"),
        },
    )
st.divider()

st.subheader(
    "Community feature PRs needing product approval",
    help="""
Feature PRs from community (`change:feature` and `impact:users`) need to be labeled with:
- `status:needs-product-approval`: Marks the PR to need a review from product before technical review.
- `status:product-approved`: PRs that have been approved by product. This is usually applied by a PM.
- `do-not-merge`: PRs that should not be merged.
""",
)
prs_needing_approval_df = get_prs_needing_product_approval()
if prs_needing_approval_df.empty:
    st.success("Congrats, everything is done here!", icon="🎉")
else:
    st.dataframe(
        prs_needing_approval_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Title": st.column_config.TextColumn("Title", width="large"),
            "URL": st.column_config.LinkColumn("URL", display_text="Open"),
            "Created": st.column_config.DatetimeColumn("Created", format="distance"),
            "Labels": st.column_config.ListColumn("Labels"),
        },
    )
st.divider()

st.subheader(
    "Community PRs ready for review",
    help="""
Lists community PRs that are ready for technical review. These PRs meet all the criteria:
- Not in draft state
- No "[WIP]" in the title
- Has both `change:*` and `impact:*` labels
- No blocking labels (`do-not-merge`, `status:needs-product-approval`, `status:awaiting-user-response`)

These PRs are ready for code review and can be prioritized for technical feedback.

Before reviewing, its recommended to approve and run the CI (check that the code doesn't contain obvious
security issues) and assign Copilot for an automated review.
""",
)
community_prs_ready_df = get_community_prs_ready_for_review()
if community_prs_ready_df.empty:
    st.success("Congrats, everything is done here!", icon="🎉")
else:
    st.dataframe(
        community_prs_ready_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Title": st.column_config.TextColumn("Title", width="large"),
            "URL": st.column_config.LinkColumn("URL", display_text="Open"),
            "Created": st.column_config.DatetimeColumn("Created", format="distance"),
            "Updated": st.column_config.DatetimeColumn("Updated", format="distance"),
            "Assignees": st.column_config.ListColumn("Assignees"),
            "Labels": st.column_config.ListColumn("Labels"),
        },
    )
st.divider()

st.subheader(
    "Open Dependabot PRs",
    help="""
Lists all open dependency update PRs from Dependabot. Please try to review and merge these PRs
if it requires no or only minor changes.

- In some cases, the PR will require manually updating the `NOTICES` file by checking out the dependency PR, running `yarn install` in `frontend`, and running `make update-notices` from repo root.
- If our CI indicates that updating the dependency will likely require bigger changes, just close the PR with a brief message and add the dependency to our https://github.com/streamlit/streamlit/blob/develop/.github/dependabot.yml ignore list. [Example PR](https://github.com/streamlit/streamlit/pull/10630)
 """,
)
dependabot_prs_df = get_open_dependabot_prs()
if dependabot_prs_df.empty:
    st.success("Congrats, everything is done here!", icon="🎉")
else:
    st.dataframe(
        dependabot_prs_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Title": st.column_config.TextColumn("Title", width="large"),
            "URL": st.column_config.LinkColumn("URL", display_text="Open"),
            "Created": st.column_config.DatetimeColumn("Created", format="distance"),
        },
    )
st.divider()

st.subheader(
    "Issues waiting for team response",
    help="Lists all issues that are waiting for a response from the team.",
)
waiting_for_team_response_df = get_issue_waiting_for_team_response()
if waiting_for_team_response_df.empty:
    st.success("Congrats, everything is done here!", icon="🎉")
else:
    st.dataframe(
        waiting_for_team_response_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Title": st.column_config.TextColumn("Title", width="large"),
            "URL": st.column_config.LinkColumn("URL", display_text="Open"),
            "Created": st.column_config.DatetimeColumn("Created", format="distance"),
            "Author": st.column_config.TextColumn("Author"),
            "Labels": st.column_config.ListColumn("Labels"),
        },
    )
st.divider()

st.subheader(
    "Flaky tests with ≥ 5 failures",
    help="""
Lists flaky tests with ≥ 5 failures in the selected timeframe.

Please try to investigate and stabilize these tests or add a `@pytest.mark.flaky(reruns=4)`
marker as a last resort.
""",
)
flaky_tests_df = get_flaky_tests(since)
# Always hide expected flaky tests
if not flaky_tests_df.empty:
    mask_not_expected = ~flaky_tests_df["Test"].apply(
        lambda t: any(t.startswith(prefix) for prefix in EXPECTED_FLAKY_TESTS)
    )
    flaky_tests_df = flaky_tests_df[mask_not_expected]

if flaky_tests_df.empty:
    st.success("Congrats, everything is done here!", icon="🎉")
else:
    flaky_tests_df = flaky_tests_df.sort_values(by="Failures", ascending=False)
    st.dataframe(
        flaky_tests_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Test": st.column_config.TextColumn("Test", width="large"),
            "Failures": st.column_config.NumberColumn("Failures"),
            "Workflow Run": st.column_config.LinkColumn(
                "Last Workflow Run", display_text="Open"
            ),
            "Last Failure Date": st.column_config.DatetimeColumn(format="distance"),
        },
    )
st.divider()

st.subheader(
    "Confirmed bugs without a reproducible script",
    help="""
Confirmed bugs (`status:confirmed` & `type:bug`) created in the selected timeframe that don't have a reproducible script.

This isn't a requirement for all issues. If the issue is not easily reproducible via the [streamlit/st-issues](https://github.com/streamlit/st-issues) app, you can skip this step.

**How to add a new repro case to [streamlit/st-issues](https://github.com/streamlit/st-issues):**
1. [Create a new folder in `issues`](https://github.com/streamlit/st-issues/new/main/issues) with this naming pattern: `gh-<GITHUB_ISSUE_ID>`.
2. Create an `app.py` file in the created issue folder and use it to reproduce the issue.
3. Once the issue is added, it should be automatically accessible from the deployed issue explorer after a page refresh.
4. Make sure to link the issue app in the respective issue on Github. Tip: Inside the Issue Description expander, you can find a markdown snippet that allows you to easily add a badge to the GitHub issue. Add this to the issue body in the Steps to reproduce section.
""",
)
confirmed_bugs_without_repro_df = get_confirmed_bugs_without_repro_script(since)
if confirmed_bugs_without_repro_df.empty:
    st.success("Congrats, everything is done here!", icon="🎉")
else:
    st.dataframe(
        confirmed_bugs_without_repro_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Title": st.column_config.TextColumn("Title", width="large"),
            "URL": st.column_config.LinkColumn("URL", display_text="Open"),
            "Created": st.column_config.DatetimeColumn("Created", format="distance"),
            "Author": st.column_config.TextColumn("Author"),
        },
    )


# Check if dialog should be shown
if st.session_state.get("show_agent_dialog", False):
    show_agent_prompt_dialog()
    # Reset the dialog trigger after showing
    st.session_state.show_agent_dialog = False
