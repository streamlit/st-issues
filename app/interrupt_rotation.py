from __future__ import annotations

import json
import pathlib
from collections import Counter
from datetime import date, datetime, timedelta
from io import BytesIO
from typing import Tuple
from zipfile import ZipFile

import humanize
import pandas as pd
import streamlit as st

from app.utils.github_utils import (
    download_artifact,
    fetch_artifacts,
    fetch_workflow_run_annotations,
    fetch_workflow_runs,
    fetch_workflow_runs_ids,
    get_all_github_issues,
    get_all_github_prs,
    is_community_author,
)

# Set page configuration
st.set_page_config(page_title="Interrupt Rotation - Dashboard", page_icon="🩺")

# Path to the issues folder
DEFAULT_ISSUES_FOLDER = "issues"
PATH_OF_SCRIPT = pathlib.Path(__file__).parent.resolve()
PATH_TO_ISSUES = (
    pathlib.Path(PATH_OF_SCRIPT).parent.joinpath(DEFAULT_ISSUES_FOLDER).resolve()
)


# Helper functions for data fetching and processing
@st.cache_data(
    ttl=60 * 60 * 6, show_spinner="Fetching python test coverage..."
)  # cache for 6 hours
def get_python_test_coverage_metrics(since_date: date) -> Tuple[float, float]:
    """Get the python test coverage and the change over a period."""
    runs_in_period = fetch_workflow_runs("python-tests.yml", since=since_date)

    def get_coverage(run_id: int) -> float:
        artifacts = fetch_artifacts(run_id)
        artifact = next(
            (a for a in artifacts if a["name"] == "combined_coverage_json"), None
        )
        if not artifact:
            return 0.0
        content = download_artifact(artifact["archive_download_url"])
        if not content:
            return 0.0
        with ZipFile(BytesIO(content)) as z:
            with z.open("coverage.json") as f:
                data = json.load(f)
                return data["totals"]["percent_covered"]

    if not runs_in_period:
        # If there are no runs in the selected period, just get the latest one
        # to show the current coverage.
        latest_run = fetch_workflow_runs("python-tests.yml", limit=1)
        if not latest_run:
            return 0.0, 0.0
        latest_coverage = get_coverage(latest_run[0]["id"])
        return latest_coverage, 0.0

    latest_coverage = get_coverage(runs_in_period[0]["id"])

    if len(runs_in_period) < 2:
        return latest_coverage, 0.0

    oldest_coverage = get_coverage(runs_in_period[-1]["id"])

    return latest_coverage, latest_coverage - oldest_coverage


@st.cache_data(
    ttl=60 * 60 * 6, show_spinner="Fetching frontend test coverage..."
)  # cache for 6 hours
def get_frontend_test_coverage_metrics(since_date: date) -> Tuple[float, float]:
    """Get the frontend test coverage and the change over a period."""
    runs_in_period = fetch_workflow_runs("js-tests.yml", since=since_date)

    def get_coverage(run_id: int) -> float:
        artifacts = fetch_artifacts(run_id)
        artifact = next(
            (a for a in artifacts if a["name"] == "vitest_coverage_json"), None
        )
        if not artifact:
            return 0.0
        content = download_artifact(artifact["archive_download_url"])
        if not content:
            return 0.0
        with ZipFile(BytesIO(content)) as z:
            json_file = next((f for f in z.namelist() if f.endswith(".json")), None)
            if json_file:
                with z.open(json_file) as f:
                    data = json.load(f)
                    return data.get("total", {}).get("lines", {}).get("pct", 0.0)
        return 0.0

    if not runs_in_period:
        # If there are no runs in the selected period, just get the latest one
        # to show the current coverage.
        latest_run = fetch_workflow_runs("js-tests.yml", limit=1)
        if not latest_run:
            return 0.0, 0.0
        latest_coverage = get_coverage(latest_run[0]["id"])
        return latest_coverage, 0.0

    latest_coverage = get_coverage(runs_in_period[0]["id"])

    if len(runs_in_period) < 2:
        return latest_coverage, 0.0

    oldest_coverage = get_coverage(runs_in_period[-1]["id"])

    return latest_coverage, latest_coverage - oldest_coverage


@st.cache_data(
    ttl=60 * 60 * 6, show_spinner="Fetching wheel size..."
)  # cache for 6 hours
def get_wheel_size_metrics(since_date: date) -> Tuple[int, int]:
    """Get the wheel size and the change over a period."""
    runs_in_period = fetch_workflow_runs("pr-preview.yml", since=since_date)

    def get_size(run_id: int) -> int:
        artifacts = fetch_artifacts(run_id)
        artifact = next((a for a in artifacts if a["name"] == "whl_file"), None)
        return artifact["size_in_bytes"] if artifact else 0

    if not runs_in_period:
        # If there are no runs in the selected period, just get the latest one
        # to show the current wheel size.
        latest_run = fetch_workflow_runs("pr-preview.yml", limit=1)
        if not latest_run:
            return 0, 0
        latest_size = get_size(latest_run[0]["id"])
        return latest_size, 0

    latest_size = get_size(runs_in_period[0]["id"])

    if len(runs_in_period) < 2:
        return latest_size, 0

    oldest_size = get_size(runs_in_period[-1]["id"])

    return latest_size, latest_size - oldest_size


def get_reproducible_example_exists(issue_number: int) -> bool:
    """Check if a reproducible example exists for an issue."""
    issue_folder_name = f"gh-{issue_number}"
    return PATH_TO_ISSUES.joinpath(issue_folder_name).is_dir()


def get_needs_triage_issues() -> pd.DataFrame:
    """Get issues that need triage."""
    issues = get_all_github_issues(state="open")
    needs_triage = []
    for i in issues:
        if "pull_request" in i:
            continue
        labels = {label["name"] for label in i["labels"]}
        if "status:needs-triage" in labels:
            needs_triage.append(
                {
                    "Title": i["title"],
                    "URL": i["html_url"],
                    "Author": i["user"]["login"],
                    "Created": i["created_at"],
                }
            )
    return pd.DataFrame(needs_triage)


def get_missing_labels_issues() -> pd.DataFrame:
    """Get issues missing feature/area labels."""
    issues = get_all_github_issues(state="open")
    missing_label_issues = []
    for i in issues:
        if "pull_request" in i:
            continue
        labels = {label["name"] for label in i["labels"]}

        if not any(
            label.startswith("feature:")
            or label.startswith("area:")
            or label == "type:kudos"
            for label in labels
        ):
            missing_label_issues.append(
                {
                    "Title": i["title"],
                    "URL": i["html_url"],
                    "Created": i["created_at"],
                    "Author": i["user"]["login"],
                    "Labels": list(labels),
                }
            )
    return pd.DataFrame(missing_label_issues)


def get_issue_waiting_for_team_response() -> pd.DataFrame:
    """Get issues waiting for team response."""
    issues = get_all_github_issues(state="open")
    waiting_for_team_response = []
    for i in issues:
        if "pull_request" in i:
            continue
        labels = {label["name"] for label in i["labels"]}
        if "status:awaiting-team-response" in labels:
            waiting_for_team_response.append(i)
    return pd.DataFrame(waiting_for_team_response)


def get_missing_labels_prs() -> pd.DataFrame:
    """Get community PRs missing change/impact labels."""
    prs = get_all_github_prs(state="open")
    missing_label_prs = []
    for pr in prs:
        author = pr.get("user", {}).get("login")
        if not author or not is_community_author(author):
            continue
        labels = {label["name"] for label in pr["labels"]}
        has_change = any(label.startswith("change:") for label in labels)
        has_impact = any(label.startswith("impact:") for label in labels)
        if not has_change or not has_impact:
            missing_label_prs.append(
                {
                    "Title": pr["title"],
                    "URL": pr["html_url"],
                    "Created": pr["created_at"],
                    "Author": author,
                    "Labels": list(labels),
                }
            )
    return pd.DataFrame(missing_label_prs)


def get_prs_needing_product_approval() -> pd.DataFrame:
    """Get community PRs with feature changes that need product approval."""
    prs = get_all_github_prs(state="open")
    needs_approval_prs = []
    for pr in prs:
        author = pr.get("user", {}).get("login")
        if not author or not is_community_author(author):
            continue

        labels = {label["name"] for label in pr["labels"]}

        has_required_labels = "change:feature" in labels and "impact:users" in labels

        has_status_labels = (
            "status:needs-product-approval" in labels
            or "status:product-approved" in labels
            or "do-not-merge" in labels
        )

        if has_required_labels and not has_status_labels:
            needs_approval_prs.append(
                {
                    "Title": pr["title"],
                    "URL": pr["html_url"],
                    "Created": pr["created_at"],
                    "Author": author,
                    "Labels": list(labels),
                }
            )
    return pd.DataFrame(needs_approval_prs)


def get_community_prs_ready_for_review() -> pd.DataFrame:
    """Get community PRs that are ready for review."""
    prs = get_all_github_prs(state="open")
    ready_for_review = []
    for pr in prs:
        author = pr.get("user", {}).get("login")
        if not author or not is_community_author(author):
            continue

        # Check if PR is in draft state
        if pr.get("draft", False):
            continue

        # Check if PR title has [WIP]
        if "[WIP]" in pr.get("title", "").upper():
            continue

        labels = {label["name"] for label in pr["labels"]}

        # Check for blocking labels
        blocking_labels = {
            "do-not-merge",
            "status:needs-product-approval",
            "status:awaiting-user-response",
        }
        if any(label in blocking_labels for label in labels):
            continue

        # Check for required labels
        has_change = any(label.startswith("change:") for label in labels)
        has_impact = any(label.startswith("impact:") for label in labels)
        if not has_change or not has_impact:
            continue

        ready_for_review.append(
            {
                "Title": pr["title"],
                "URL": pr["html_url"],
                "Assignees": [
                    assignee["login"] for assignee in pr.get("assignees", [])
                ],
                "Created": pr["created_at"],
                "Updated": pr["updated_at"],
                "Labels": list(labels),
                "Author": author,
            }
        )
    return pd.DataFrame(ready_for_review)


def get_unprioritized_bugs() -> pd.DataFrame:
    """Get confirmed bugs without a priority."""
    issues = get_all_github_issues(state="open")
    unprioritized = []
    for i in issues:
        if "pull_request" in i:
            continue
        labels = {label["name"] for label in i["labels"]}
        if "type:bug" in labels and "status:confirmed" in labels:
            has_priority = any(label.startswith("priority:P") for label in labels)
            if not has_priority:
                unprioritized.append(
                    {
                        "Title": i["title"],
                        "URL": i["html_url"],
                        "Created": i["created_at"],
                        "Author": i["user"]["login"],
                    }
                )
    return pd.DataFrame(unprioritized)


def get_p0_p1_bugs() -> pd.DataFrame:
    """Get all P0 and P1 priority bugs."""
    issues = get_all_github_issues(state="open")
    high_priority_bugs = []
    for i in issues:
        if "pull_request" in i:
            continue
        labels = {label["name"] for label in i["labels"]}
        if "type:bug" in labels and any(
            label in ["priority:P0", "priority:P1"] for label in labels
        ):
            priority = next(
                (label for label in labels if label.startswith("priority:P")), "Unknown"
            )
            high_priority_bugs.append(
                {
                    "Title": i["title"],
                    "URL": i["html_url"],
                    "Created": i["created_at"],
                    "Assignees": [
                        assignee["login"] for assignee in i.get("assignees", [])
                    ],
                    "Priority": priority,
                    "Labels": list(labels),
                    "Author": i["user"]["login"],
                }
            )
    return pd.DataFrame(high_priority_bugs)


def get_confirmed_bugs_without_repro_script(since_date: date) -> pd.DataFrame:
    """Get confirmed bugs created since a date that don't have a repro script."""
    issues = get_all_github_issues(state="open")  # Get all open issues
    bugs_without_repro = []
    for i in issues:
        if "pull_request" in i:
            continue

        created_at = datetime.fromisoformat(i["created_at"].replace("Z", "+00:00"))
        if created_at.date() < since_date:
            continue

        labels = {label["name"] for label in i["labels"]}
        if (
            "type:bug" in labels
            and "status:confirmed" in labels
            # Multipage app bugs are not easy to reproduce
            # in the issues app:
            and "feature:multipage-apps" not in labels
        ):
            if not get_reproducible_example_exists(i["number"]):
                bugs_without_repro.append(
                    {
                        "Title": i["title"],
                        "URL": i["html_url"],
                        "Created": i["created_at"],
                        "Author": i["user"]["login"],
                    }
                )
    return pd.DataFrame(bugs_without_repro)


@st.cache_data(ttl=60 * 60 * 6)  # cache for 6 hours
def get_flaky_tests(since_date: date) -> pd.DataFrame:
    """Get flaky tests with >= 5 failures."""
    flaky_tests_counter: Counter[str] = Counter()
    example_run: dict[str, str] = {}
    last_failure_date: dict[str, date] = {}

    workflow_runs = fetch_workflow_runs(
        "playwright.yml", since=since_date, status="success", branch=None, limit=200
    )

    for run in workflow_runs:
        check_run_ids = fetch_workflow_runs_ids(run["check_suite_id"])
        for check_run_id in check_run_ids:
            annotations = fetch_workflow_run_annotations(check_run_id)
            for annotation in annotations:
                if annotation["path"].startswith("e2e_playwright/"):
                    test_name = (
                        f"{annotation['path'].replace('e2e_playwright/', '')}::"
                        + annotation["message"].split("\n\n")[0]
                    )
                    flaky_tests_counter.update([test_name])
                    if test_name not in example_run:
                        example_run[test_name] = run["html_url"]

                    if test_name not in last_failure_date:
                        last_failure_date[test_name] = date.fromisoformat(
                            run["created_at"][:10]
                        )

    data = [
        {
            "Test": test,
            "Failures": count,
            "Workflow Run": example_run[test],
            "Last Failure Date": last_failure_date[test],
        }
        for test, count in flaky_tests_counter.items()
        # Should be atleast 5 failures and the last failure should be in the last 4 days
        if count >= 5 and last_failure_date[test] > date.today() - timedelta(days=4)
    ]
    return pd.DataFrame(data)


def get_open_dependabot_prs() -> pd.DataFrame:
    """Get open Dependabot PRs without 'do-not-merge' label."""
    prs = get_all_github_prs(state="open")
    dependabot_prs = []
    for pr in prs:
        author = pr.get("user", {}).get("login")
        if author == "dependabot[bot]":
            labels = {label["name"] for label in pr["labels"]}
            if "do-not-merge" not in labels:
                dependabot_prs.append(
                    {
                        "Title": pr["title"],
                        "URL": pr["html_url"],
                        "Created": pr["created_at"],
                    }
                )
    return pd.DataFrame(dependabot_prs)


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
    )
with col2:
    fe_coverage, fe_coverage_change = get_frontend_test_coverage_metrics(since)
    st.metric(
        "Frontend Test Coverage",
        f"{fe_coverage:.2f}%",
        f"{fe_coverage_change:+.2f}%",
        delta_color="normal",
        border=True,
    )
with col3:
    wheel_size, wheel_size_change = get_wheel_size_metrics(since)
    st.metric(
        "Wheel Size",
        humanize.naturalsize(wheel_size, binary=True),
        humanize.naturalsize(wheel_size_change, binary=True),
        delta_color="inverse",
        border=True,
    )


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
        p0_p1_bugs_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Title": st.column_config.TextColumn("Title", width="large"),
            "URL": st.column_config.LinkColumn("URL", display_text="Open"),
            "Created": st.column_config.DatetimeColumn("Created", format="distance"),
            "Assignees": st.column_config.ListColumn("Assignees"),
            "Priority": st.column_config.TextColumn("Priority"),
            "Labels": st.column_config.ListColumn("Labels"),
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
        waiting_for_team_response_df, use_container_width=True, hide_index=True
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
        },
    )
