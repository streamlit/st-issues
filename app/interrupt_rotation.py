from __future__ import annotations

from datetime import date, timedelta

import humanize
import pandas as pd
import streamlit as st

from app.utils.github_utils import (
    EXPECTED_FLAKY_TESTS,
)
from app.utils.interrupt_data import (
    BOT_PR_INTERRUPT_REPOS,
    DEVELOP_COMMIT_WINDOW,
    JS_UNIT_TESTS_JOB,
    MONITORED_INTERRUPT_REPOS,
    PYTHON_UNIT_TESTS_MAX_JOB,
    build_interrupt_action_items,
    clear_interrupt_caches,
    get_bundle_size_metrics,
    get_ci_failing_test_run_metrics,
    get_ci_test_annotations,
    get_confirmed_bugs_without_repro_script,
    get_dependabot_alerts,
    get_flaky_tests,
    get_frontend_test_coverage_metrics,
    get_monitored_repo_open_prs,
    get_nightly_run_metrics,
    get_playwright_test_count_metrics,
    get_python_test_coverage_metrics,
    get_reported_bugs,
    get_wheel_size_metrics,
)

# Set page configuration
st.set_page_config(page_title="Interrupt rotation", page_icon=":material/stethoscope:", layout="wide")

# SLA targets (in days) for high-priority bugs, measured from the issue creation date.
HIGH_PRIORITY_SLA_DAYS = {"priority:P0": 1, "priority:P1": 7, "priority:P2": 14}
HIGH_PRIORITY_SLA_LABELS = {
    "priority:P0": "≤ 1 day",
    "priority:P1": "≤ 1 week",
    "priority:P2": "≤ 2 weeks",
}

# CI metric warning thresholds. Coverage is percent-covered; sizes are binary bytes
# (1024-based), matching humanize.naturalsize(..., binary=True).
PYTHON_COVERAGE_WARNING_PCT = 97.0
FRONTEND_COVERAGE_WARNING_PCT = 94.0
WHEEL_SIZE_WARNING_BYTES = 12 * 1024 * 1024
TOTAL_BUNDLE_WARNING_BYTES = 10 * 1024 * 1024
ENTRY_BUNDLE_WARNING_BYTES = 500 * 1024
CI_FAILING_TEST_WARNING_PCT = 1.0
FLAKY_TEST_MIN_FAILURES = 5


def _metric_text(text: str, *, warn: bool) -> str:
    """Return metric label or value text, colored red when the warning threshold is breached."""
    return f":red[{text}]" if warn else text


def _metric_icon(*, warn: bool) -> str | None:
    """Return a warning icon when the metric is outside its healthy range."""
    return ":material/warning:" if warn else None


@st.fragment(parallel=True)
def render_ci_metrics(selected_since: date) -> None:
    col1, col2, col3, col4 = st.columns(4)
    with col1, st.skeleton(height=110):
        py_coverage, py_coverage_change = get_python_test_coverage_metrics(selected_since)
        py_coverage_warn = py_coverage < PYTHON_COVERAGE_WARNING_PCT
        st.metric(
            _metric_text("Python Test Coverage", warn=py_coverage_warn),
            _metric_text(f"{py_coverage:.2f}%", warn=py_coverage_warn),
            f"{py_coverage_change:+.2f}%",
            delta_color="normal",
            delta_arrow="off",
            border=True,
            icon=_metric_icon(warn=py_coverage_warn),
            help=(
                "Percentage of lines covered by tests in the Python codebase. "
                f"A warning is shown when coverage is below {PYTHON_COVERAGE_WARNING_PCT:.0f}%."
            ),
        )
    with col2, st.skeleton(height=110):
        fe_coverage, fe_coverage_change = get_frontend_test_coverage_metrics(selected_since)
        fe_coverage_warn = fe_coverage < FRONTEND_COVERAGE_WARNING_PCT
        st.metric(
            _metric_text("Frontend Test Coverage", warn=fe_coverage_warn),
            _metric_text(f"{fe_coverage:.2f}%", warn=fe_coverage_warn),
            f"{fe_coverage_change:+.2f}%",
            delta_color="normal",
            delta_arrow="off",
            border=True,
            icon=_metric_icon(warn=fe_coverage_warn),
            help=(
                "Percentage of lines covered by tests in the Frontend codebase. "
                f"A warning is shown when coverage is below {FRONTEND_COVERAGE_WARNING_PCT:.0f}%."
            ),
        )
    with col3, st.skeleton(height=110):
        wheel_size, wheel_size_change = get_wheel_size_metrics(selected_since)
        wheel_size_warn = wheel_size > WHEEL_SIZE_WARNING_BYTES
        st.metric(
            _metric_text("Wheel Size", warn=wheel_size_warn),
            _metric_text(humanize.naturalsize(wheel_size, binary=True), warn=wheel_size_warn),
            humanize.naturalsize(wheel_size_change, binary=True),
            delta_color="inverse",
            delta_arrow="off",
            border=True,
            icon=_metric_icon(warn=wheel_size_warn),
            help=("Size of the Streamlit Python package (wheel file). A warning is shown when the size is above 12MB."),
        )
    with col4, st.skeleton(height=110):
        (
            total_gzip,
            total_gzip_change,
            entry_gzip,
            entry_gzip_change,
        ) = get_bundle_size_metrics(selected_since)

        total_gzip_warn = total_gzip > TOTAL_BUNDLE_WARNING_BYTES
        st.metric(
            _metric_text("Total Bundle (gzip)", warn=total_gzip_warn),
            _metric_text(humanize.naturalsize(total_gzip, binary=True), warn=total_gzip_warn),
            humanize.naturalsize(total_gzip_change, binary=True),
            delta_color="inverse",
            delta_arrow="off",
            border=True,
            icon=_metric_icon(warn=total_gzip_warn),
            help=(
                "Total size of all JavaScript files after Gzip compression. "
                "A warning is shown when the size is above 10MB."
            ),
        )

    col1, col2, col3, col4 = st.columns(4)
    with col1, st.skeleton(height=110):
        entry_gzip_warn = entry_gzip > ENTRY_BUNDLE_WARNING_BYTES
        st.metric(
            _metric_text("Entry Bundle (gzip)", warn=entry_gzip_warn),
            _metric_text(humanize.naturalsize(entry_gzip, binary=True), warn=entry_gzip_warn),
            humanize.naturalsize(entry_gzip_change, binary=True),
            delta_color="inverse",
            delta_arrow="off",
            border=True,
            icon=_metric_icon(warn=entry_gzip_warn),
            help=(
                "Size of the entry point chunks (initial load) after Gzip compression. "
                "A warning is shown when the size is above 500KB."
            ),
        )
    with col2, st.skeleton(height=110):
        pw_count, pw_count_change = get_playwright_test_count_metrics(selected_since)
        st.metric(
            "Playwright Tests",
            f"{pw_count:,}",
            f"{pw_count_change:+,}",
            delta_color="off",
            delta_arrow="off",
            border=True,
            help="Total number of Playwright E2E tests (across all browsers).",
        )
    with col3, st.skeleton(height=110):
        failing_pct, failing_checks, total_checks, *_ = get_ci_failing_test_run_metrics()
        failing_pct_warn = total_checks > 0 and failing_pct > CI_FAILING_TEST_WARNING_PCT
        st.metric(
            _metric_text("Failed CI Checks", warn=failing_pct_warn),
            _metric_text(f"{failing_pct:.0f}%", warn=failing_pct_warn),
            _metric_text(f"{failing_checks}/{total_checks} checks", warn=failing_checks > 0),
            delta_color="off",
            delta_arrow="off",
            border=True,
            icon=_metric_icon(warn=failing_pct_warn),
            help=(
                "Percentage of GitHub checks on the last "
                f"{DEVELOP_COMMIT_WINDOW} commits to `develop` that failed. "
                "This includes every CheckRun and commit status on those commits "
                "(not only Python, frontend, or Playwright workflows). "
                "Skipped, cancelled, neutral, and in-progress checks are ignored. "
                "This ignores the timeframe selector. "
                f"A warning is shown when the rate is over {CI_FAILING_TEST_WARNING_PCT:.0f}%."
            ),
        )
    with col4, st.skeleton(height=110):
        nightly_pct, nightly_failing, nightly_total = get_nightly_run_metrics(selected_since)
        nightly_warn = nightly_failing > 0
        nightly_delta = f"{nightly_pct:.0f}% · {nightly_failing}/{nightly_total} runs" if nightly_total else "0/0 runs"
        st.metric(
            _metric_text("Failed Nightly Runs", warn=nightly_warn),
            _metric_text(str(nightly_failing), warn=nightly_warn),
            _metric_text(nightly_delta, warn=nightly_warn),
            delta_color="off",
            delta_arrow="off",
            border=True,
            icon=_metric_icon(warn=nightly_warn),
            help=(
                "Number of failed [`nightly.yml`](https://github.com/streamlit/streamlit/actions/"
                "workflows/nightly.yml) runs on `develop` in the selected timeframe. "
                "The delta shows the failure rate and failed/total completed runs. "
                "Skipped, cancelled, and in-progress runs are ignored. "
                "A warning is shown when any nightly run failed."
            ),
        )


@st.fragment(parallel=True)
def render_issue_action_items(selected_since: date) -> None:
    """Render the issue-focused action-item tables (top of the Action Items list).

    This is one of two parallel fragments that read the shared action-items
    snapshot; this one renders the issue tables and render_community_pr_action_items
    renders the PR tables lower on the page. build_interrupt_action_items is memoized
    by st.cache_data, so it is computed once and the sibling fragment's call is a
    cache hit rather than a second fetch. Running as a parallel fragment lets the
    snapshot fetch overlap with the other parallel fragments during a full rerun.
    """
    with st.skeleton(height=600):
        action_items = build_interrupt_action_items(since_date=selected_since)

        st.subheader(
            "High-priority bugs (P0, P1, P2)",
            help="""
Lists high-priority bugs that require attention within their SLA.
Please make sure that these bugs are assigned and are being worked on.

**SLAs (measured from the issue creation date):**
- **P0:** fix within **1 day**
- **P1:** fix within **1 week**
- **P2:** fix within **2 weeks**

The **SLA Due** column shows when the SLA is (or was) due and the **SLA Status** column
indicates whether a bug is still within its SLA or has already breached it.
""",
        )
        high_priority_bugs_df = action_items["high_priority_bugs"].copy()
        if high_priority_bugs_df.empty:
            st.success("Congrats, everything is done here!", icon=":material/celebration:")
        else:
            # Sort by priority (P0 first, then P1, then P2) and then by creation date (oldest first).
            high_priority_bugs_df["Priority_Sort"] = high_priority_bugs_df["Priority"].map(
                {"priority:P0": 0, "priority:P1": 1, "priority:P2": 2}
            )
            high_priority_bugs_df = high_priority_bugs_df.sort_values(by=["Priority_Sort", "Created"])

            # Compute SLA info based on the creation date and the priority-specific SLA target.
            created_ts = pd.to_datetime(high_priority_bugs_df["Created"], utc=True)
            sla_days = high_priority_bugs_df["Priority"].map(HIGH_PRIORITY_SLA_DAYS)
            sla_due_ts = created_ts + pd.to_timedelta(sla_days, unit="D")
            is_breached = pd.Timestamp.now(tz="UTC") > sla_due_ts

            high_priority_bugs_df["SLA"] = high_priority_bugs_df["Priority"].map(HIGH_PRIORITY_SLA_LABELS)
            high_priority_bugs_df["SLA Due"] = sla_due_ts
            high_priority_bugs_df["SLA Status"] = [
                ["Breached"] if breached else ["Within SLA"] for breached in is_breached
            ]

            # Wrap the priority in a list so it can be rendered as a colored chip via MultiselectColumn.
            high_priority_bugs_df["Priority"] = high_priority_bugs_df["Priority"].map(lambda priority: [priority])

            high_priority_bugs_df = high_priority_bugs_df.drop("Priority_Sort", axis=1)

            st.dataframe(
                high_priority_bugs_df,
                width="stretch",
                hide_index=True,
                column_order=[
                    "Title",
                    "URL",
                    "Priority",
                    "Created",
                    "SLA",
                    "SLA Due",
                    "SLA Status",
                    "Assignees",
                ],
                column_config={
                    "Title": st.column_config.TextColumn("Title", width="large"),
                    "URL": st.column_config.LinkColumn("URL", display_text="Open"),
                    "Priority": st.column_config.MultiselectColumn(
                        "Priority",
                        options=[
                            "priority:P0",
                            "priority:P1",
                            "priority:P2",
                            "priority:P3",
                            "priority:P4",
                        ],
                        color=["red", "orange", "yellow", "blue", "gray"],
                        format_func=lambda label: label.removeprefix("priority:"),
                    ),
                    "Created": st.column_config.DatetimeColumn("Created", format="distance"),
                    "SLA": st.column_config.TextColumn("SLA", help="SLA target based on the bug's priority."),
                    "SLA Due": st.column_config.DatetimeColumn(
                        "SLA Due",
                        format="distance",
                        help="When the SLA is (or was) due, based on the creation date.",
                    ),
                    "SLA Status": st.column_config.MultiselectColumn(
                        "SLA Status",
                        options=["Within SLA", "Breached"],
                        color=["green", "red"],
                    ),
                    "Assignees": st.column_config.ListColumn("Assignees"),
                },
            )

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
        needs_triage_df = action_items["needs_triage"]
        if needs_triage_df.empty:
            st.success("Congrats, everything is done here!", icon=":material/celebration:")
        else:
            st.dataframe(
                needs_triage_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Title": st.column_config.TextColumn("Title", width="large"),
                    "URL": st.column_config.LinkColumn("URL", display_text="Open"),
                    "Created": st.column_config.DatetimeColumn("Created", format="distance"),
                    "Author": st.column_config.TextColumn("Author"),
                },
            )

        st.subheader(
            "Issues missing feature label",
            help="Every issue is expected to have at least one `feature:{the_feature}` or `area:{the_area}` label.",
        )
        missing_labels_df = action_items["missing_labels_issues"]
        if missing_labels_df.empty:
            st.success("Congrats, everything is done here!", icon=":material/celebration:")
        else:
            st.dataframe(
                missing_labels_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Title": st.column_config.TextColumn("Title", width="large"),
                    "URL": st.column_config.LinkColumn("URL", display_text="Open"),
                    "Created": st.column_config.DatetimeColumn("Created", format="distance"),
                    "Author": st.column_config.TextColumn("Author"),
                    "Labels": st.column_config.ListColumn("Labels"),
                },
            )

        st.subheader(
            "Confirmed bugs without a priority",
            help="""
Every confirmed bug is expected to be labeled with a `priority:P{0,1,2,3,4}` label.

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
        unprioritized_bugs_df = action_items["unprioritized_bugs"]
        if unprioritized_bugs_df.empty:
            st.success("Congrats, everything is done here!", icon=":material/celebration:")
        else:
            st.dataframe(
                unprioritized_bugs_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Title": st.column_config.TextColumn("Title", width="large"),
                    "URL": st.column_config.LinkColumn("URL", display_text="Open"),
                    "Created": st.column_config.DatetimeColumn("Created", format="distance"),
                    "Author": st.column_config.TextColumn("Author"),
                },
            )

        st.subheader(
            "Open release PRs",
            help="""
Lists open automated release PRs (`[chore] Release vX.Y.Z` from `github-actions[bot]`).
These back-merge the release branch into `develop` and only update version identifiers
(`lib/pyproject.toml`, `uv.lock`, `frontend/package.json` and the frontend workspace packages).

These PRs need a human approval before they become mergeable and are not assigned to anyone
by default, so they can sit unnoticed. The Interrupt should make sure each one gets reviewed
and merged.
""",
        )
        release_prs_df = action_items["open_release_prs"]
        if release_prs_df.empty:
            st.success("Congrats, everything is done here!", icon=":material/celebration:")
        else:
            st.dataframe(
                release_prs_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Title": st.column_config.TextColumn("Title", width="large"),
                    "URL": st.column_config.LinkColumn("URL", display_text="Open"),
                    "Created": st.column_config.DatetimeColumn("Created", format="distance"),
                },
            )

        st.subheader(
            "Open bot PRs",
            help="""
Lists all open PRs from bots (Dependabot, GitHub Actions, etc.) in `streamlit/streamlit`, excluding
automated release PRs which have their own section above. Please try to review and merge these PRs
if it requires no or only minor changes. Dependabot and GitHub Actions PRs from other Streamlit
repos such as `streamlit/docs` are listed under Open PRs in important repos instead.

For Dependabot dependency updates:
- In some cases, the PR will require manually updating the `NOTICES` file by checking out the dependency PR, running `yarn install` in `frontend`, and running `make update-notices` from repo root.
- If our CI indicates that updating the dependency will likely require bigger changes, just close the PR with a brief message and add the dependency to our https://github.com/streamlit/streamlit/blob/develop/.github/dependabot.yml ignore list. [Example PR](https://github.com/streamlit/streamlit/pull/10630)
 """,
        )
        bot_prs_df = action_items["open_bot_prs"]
        if bot_prs_df.empty:
            st.success("Congrats, everything is done here!", icon=":material/celebration:")
        else:
            st.dataframe(
                bot_prs_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Title": st.column_config.TextColumn("Title", width="large"),
                    "URL": st.column_config.LinkColumn("URL", display_text="Open"),
                    "Created": st.column_config.DatetimeColumn("Created", format="distance"),
                    "Author": st.column_config.TextColumn("Author"),
                },
            )

        st.subheader(
            "Issues waiting for team response",
            help="Lists all issues that are waiting for a response from the team.",
        )
        waiting_for_team_response_df = action_items["waiting_for_team_response"]
        if waiting_for_team_response_df.empty:
            st.success("Congrats, everything is done here!", icon=":material/celebration:")
        else:
            st.dataframe(
                waiting_for_team_response_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Title": st.column_config.TextColumn("Title", width="large"),
                    "URL": st.column_config.LinkColumn("URL", display_text="Open"),
                    "Created": st.column_config.DatetimeColumn("Created", format="distance"),
                    "Author": st.column_config.TextColumn("Author"),
                    "Labels": st.column_config.ListColumn("Labels"),
                },
            )


@st.fragment(parallel=True)
def render_flaky_tests(selected_since: date) -> None:
    st.subheader(
        f"Flaky tests with ≥ {FLAKY_TEST_MIN_FAILURES} failures",
        help=f"""
Lists flaky tests with ≥ {FLAKY_TEST_MIN_FAILURES} failures in the selected timeframe.

Please try to investigate and stabilize these tests or add a `@pytest.mark.flaky(reruns=3)`
marker as a last resort.
""",
    )
    with st.skeleton(height=200):
        flaky_tests_df = get_flaky_tests(
            selected_since,
            min_failures=FLAKY_TEST_MIN_FAILURES,
        )
        # Always hide expected flaky tests
        if not flaky_tests_df.empty:
            mask_not_expected = ~flaky_tests_df["Test"].apply(
                lambda t: any(t.startswith(prefix) for prefix in EXPECTED_FLAKY_TESTS)
            )
            flaky_tests_df = flaky_tests_df[mask_not_expected]

        if flaky_tests_df.empty:
            st.success("Congrats, everything is done here!", icon=":material/celebration:")
        else:
            flaky_tests_df = flaky_tests_df.sort_values(by="Failures", ascending=False)
            st.dataframe(
                flaky_tests_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Test": st.column_config.TextColumn("Test", width="large"),
                    "Failures": st.column_config.NumberColumn("Failures"),
                    "Workflow Run": st.column_config.LinkColumn("Last Workflow Run", display_text="Open"),
                    "Last Failure Date": st.column_config.DatetimeColumn(format="distance"),
                },
            )


@st.fragment(parallel=True)
def render_ci_test_annotations() -> None:
    annotations_help = """
Lists unique check-run annotations from the latest successful unit-test jobs on `develop`:
- `python-tests.yml` → `py-unit-tests (max)` (newest Python)
- `js-tests.yml` → `js-unit-tests`

These include deprecation warnings, resource warnings, errors that did not fail the job,
and tool notices (for example Knip). Please investigate and fix them so the next run is clean.

This ignores the timeframe selector.
"""
    header = st.empty()
    header.subheader("CI test annotations", help=annotations_help)
    with st.skeleton(height=200):
        annotations_df, sources = get_ci_test_annotations()
        source_links = [f"[`{source['job']}`]({source['job_url']})" for source in sources if source.get("job_url")]
        if source_links:
            header.subheader(
                "CI test annotations",
                help=annotations_help + "\nLatest successful runs on `develop`: " + " · ".join(source_links),
            )

        missing_jobs = [source["job"] for source in sources if not source.get("job_url")]
        if missing_jobs:
            st.warning(
                "Could not find the latest successful "
                + " / ".join(f"`{job}`" for job in missing_jobs)
                + " job on `develop`."
            )

        if annotations_df.empty:
            if not missing_jobs:
                st.success("Congrats, everything is done here!", icon=":material/celebration:")
        else:
            annotations_df = annotations_df.copy()
            annotations_df["Level"] = annotations_df["Level"].map(lambda level: [level])
            annotations_df["Job"] = annotations_df["Job"].map(lambda job: [job])
            st.dataframe(
                annotations_df,
                width="stretch",
                hide_index=True,
                column_order=["Level", "Job", "Message", "Location", "Count", "URL"],
                column_config={
                    "Level": st.column_config.MultiselectColumn(
                        "Level",
                        options=["error", "warning", "notice"],
                        color=["red", "orange", "blue"],
                    ),
                    "Job": st.column_config.MultiselectColumn(
                        "Job",
                        options=[PYTHON_UNIT_TESTS_MAX_JOB, JS_UNIT_TESTS_JOB],
                    ),
                    "Message": st.column_config.TextColumn("Message", width="large"),
                    "Location": st.column_config.TextColumn("Location"),
                    "Count": st.column_config.NumberColumn("Count"),
                    "URL": st.column_config.LinkColumn("Job", display_text="Open"),
                },
            )


@st.fragment(parallel=True)
def render_dependabot_alerts() -> None:
    st.subheader(
        "Dependabot alerts",
        help="""
Open Dependabot alerts for `streamlit/streamlit`. Please investigate and get this list to 0:
bump the dependency or merge a Dependabot PR.

If an alert isn't fixable and the dependency is unused, it is fine to dismiss the alert instead.

Open alerts: [streamlit/streamlit Dependabot](https://github.com/streamlit/streamlit/security/dependabot?q=is%3Aopen)

The GitHub token needs the `security_events` scope (classic) or Dependabot alerts read permission.
This ignores the timeframe selector.
""",
    )
    with st.skeleton(height=200):
        alerts_df = get_dependabot_alerts()
        if alerts_df.empty:
            st.success("Congrats, everything is done here!", icon=":material/celebration:")
        else:
            alerts_df = alerts_df.copy()
            alerts_df["Severity"] = alerts_df["Severity"].map(lambda severity: [severity])
            st.dataframe(
                alerts_df,
                width="stretch",
                hide_index=True,
                column_order=[
                    "Severity",
                    "Package",
                    "Ecosystem",
                    "Manifest",
                    "Summary",
                    "Advisory",
                    "Patched",
                    "Created",
                    "URL",
                ],
                column_config={
                    "Severity": st.column_config.MultiselectColumn(
                        "Severity",
                        options=["critical", "high", "medium", "low"],
                        color=["red", "orange", "yellow", "blue"],
                    ),
                    "Package": st.column_config.TextColumn("Package"),
                    "Ecosystem": st.column_config.TextColumn("Ecosystem"),
                    "Manifest": st.column_config.TextColumn("Manifest"),
                    "Summary": st.column_config.TextColumn("Summary", width="large"),
                    "Advisory": st.column_config.TextColumn("Advisory"),
                    "Patched": st.column_config.TextColumn("Patched"),
                    "Created": st.column_config.DatetimeColumn("Created", format="distance"),
                    "URL": st.column_config.LinkColumn("Alert", display_text="Open"),
                },
            )


@st.fragment(parallel=True)
def render_monitored_repo_prs() -> None:
    monitored_repos_help = "\n".join(f"- `{repo}`" for repo in MONITORED_INTERRUPT_REPOS)
    bot_only_repos_help = "\n".join(
        f"- `{repo}` (Dependabot and GitHub Actions PRs only)"
        for repo in BOT_PR_INTERRUPT_REPOS
        if repo not in MONITORED_INTERRUPT_REPOS
    )
    st.subheader(
        "Open PRs in important repos",
        help=(
            "Track open pull requests in Streamlit-maintained repos that may need interrupt "
            "rotation attention.\n\n"
            "Only PRs that are ready for review appear here. If a PR is not ready, mark it as "
            "draft so it does not show up in this view.\n\n"
            "Interrupt may need to review, approve, and merge PRs for these repos.\n\n"
            "If any PR shown in this view should really be tracked as a GitHub issue in "
            "`streamlit/streamlit` instead, close the PR (or move it back to draft) and ask the "
            "user to open an issue or feature request in `streamlit/streamlit`.\n\n"
            "Monitored repos:\n" + monitored_repos_help + ("\n" + bot_only_repos_help if bot_only_repos_help else "")
        ),
    )
    with st.skeleton(height=200):
        monitored_repo_prs_df = get_monitored_repo_open_prs()
        monitored_repo_prs_df = (
            monitored_repo_prs_df[~monitored_repo_prs_df["Draft"]]
            if not monitored_repo_prs_df.empty
            else monitored_repo_prs_df
        )
        if monitored_repo_prs_df.empty:
            st.success("Congrats, everything is done here!", icon=":material/celebration:")
        else:
            st.dataframe(
                monitored_repo_prs_df[["Title", "Repository", "URL", "Created", "Updated", "Author"]],
                width="stretch",
                hide_index=True,
                column_config={
                    "Title": st.column_config.TextColumn("Title", width="large"),
                    "Repository": st.column_config.TextColumn("Repository", width="medium"),
                    "URL": st.column_config.LinkColumn("URL", display_text="Open"),
                    "Created": st.column_config.DatetimeColumn("Created", format="distance"),
                    "Updated": st.column_config.DatetimeColumn("Updated", format="distance"),
                    "Author": st.column_config.TextColumn("Author"),
                },
            )


@st.fragment(parallel=True)
def render_confirmed_bugs_without_repro(selected_since: date) -> None:
    st.subheader(
        "Confirmed bugs without a reproducible script",
        help="""
Confirmed bugs (`status:confirmed` & `type:bug`) created in the selected timeframe that don't have a reproducible script.

**"Reproducible script" here means a runnable repro committed by the team**, either a `gh-<issue-id>` folder in [streamlit/st-issues](https://github.com/streamlit/st-issues) or an `issues/<issue-id>/repro_app.py` in the agent wiki. It does **not** mean the "Reproducible Code Example" snippet in the issue body - most issues have that from the bug-report template, so it doesn't count here.

This view is informational only - no action is required. Adding a reproducible script is best-effort: if a bug isn't easily reproducible via the [streamlit/st-issues](https://github.com/streamlit/st-issues) app, it's fine to skip writing a script.

**How to add a new repro case to [streamlit/st-issues](https://github.com/streamlit/st-issues):**
1. [Create a new folder in `issues`](https://github.com/streamlit/st-issues/new/main/issues) with this naming pattern: `gh-<GITHUB_ISSUE_ID>`.
2. Create an `app.py` file in the created issue folder and use it to reproduce the issue.
3. Once the issue is added, it should be automatically accessible from the deployed issue explorer after a page refresh.
4. Make sure to link the issue app in the respective issue on Github. Tip: Inside the Issue Description expander, you can find a markdown snippet that allows you to easily add a badge to the GitHub issue. Add this to the issue body in the Steps to reproduce section.
""",
    )
    with st.skeleton(height=200):
        confirmed_bugs_without_repro_df = get_confirmed_bugs_without_repro_script(selected_since)
        if confirmed_bugs_without_repro_df.empty:
            st.caption("Nothing to show right now.")
        else:
            st.dataframe(
                confirmed_bugs_without_repro_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Title": st.column_config.TextColumn("Title", width="large"),
                    "URL": st.column_config.LinkColumn("URL", display_text="Open"),
                    "Created": st.column_config.DatetimeColumn("Created", format="distance"),
                    "Author": st.column_config.TextColumn("Author"),
                },
            )


@st.fragment(parallel=True)
def render_reported_bugs(selected_since: date) -> None:
    st.subheader(
        "Bugs reported in the timeframe",
        help=(
            "Lists all bugs (labeled `type:bug`) that were reported in the selected timeframe, "
            "regardless of whether they are still open or already closed. Useful for tracking the "
            "overall bug influx during the interrupt rotation."
        ),
    )
    with st.skeleton(height=200):
        reported_bugs_df = get_reported_bugs(selected_since)
        if reported_bugs_df.empty:
            st.success("No bugs were reported in the selected timeframe.", icon=":material/celebration:")
        else:
            st.dataframe(
                reported_bugs_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Title": st.column_config.TextColumn("Title", width="large"),
                    "URL": st.column_config.LinkColumn("URL", display_text="Open"),
                    "State": st.column_config.MultiselectColumn(
                        "State",
                        options=["open", "closed"],
                        color=["green", "gray"],
                        format_func=lambda state: state.capitalize(),
                    ),
                    "Priority": st.column_config.MultiselectColumn(
                        "Priority",
                        options=[
                            "priority:P0",
                            "priority:P1",
                            "priority:P2",
                            "priority:P3",
                            "priority:P4",
                        ],
                        color=["red", "orange", "yellow", "blue", "gray"],
                        format_func=lambda label: label.removeprefix("priority:"),
                    ),
                    "Confirmed": st.column_config.CheckboxColumn(
                        "Confirmed",
                        help="Whether the bug has the `status:confirmed` label.",
                    ),
                    "Created": st.column_config.DatetimeColumn("Created", format="distance"),
                    "Author": st.column_config.TextColumn("Author"),
                    "Labels": st.column_config.ListColumn("Labels"),
                },
            )


@st.fragment(parallel=True)
def render_community_pr_action_items(selected_since: date) -> None:
    """Render the community-PR action-item tables (bottom of the Action Items list).

    This is one of two parallel fragments that read the shared action-items
    snapshot; render_issue_action_items renders the issue tables higher on the page
    and this one renders the PR tables. build_interrupt_action_items is memoized by
    st.cache_data, so it is computed once and this fragment's call is a cache hit
    rather than a second fetch. Splitting the tables across two fragments keeps the
    original page order (issue tables at the top, PR tables at the bottom, with the
    independent-source sections in between) while still overlapping the snapshot
    fetch with the other parallel fragments.
    """
    with st.skeleton(height=400):
        action_items = build_interrupt_action_items(since_date=selected_since)

        st.info(
            "We no longer accept new community PRs. The views below are read-only and "
            "informational - no action is required from the person on Interrupt.",
            icon=":material/info:",
        )

        st.subheader(
            "Community PRs missing labels",
            help="Every community PR is expected to be labeled with a `change:*` and `impact:*` label.",
        )
        missing_labels_prs_df = action_items["missing_labels_prs"]
        if missing_labels_prs_df.empty:
            st.caption("Nothing to show right now.")
        else:
            st.dataframe(
                missing_labels_prs_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Title": st.column_config.TextColumn("Title", width="large"),
                    "URL": st.column_config.LinkColumn("URL", display_text="Open"),
                    "Created": st.column_config.DatetimeColumn("Created", format="distance"),
                    "Labels": st.column_config.ListColumn("Labels"),
                },
            )

        st.subheader(
            "Community feature PRs needing product approval labels",
            help="""
Feature PRs from community (`change:feature` and `impact:users`) need to be labeled with:
- `status:needs-product-approval`: Marks the PR to need a review from product before technical review.
- `status:product-approved`: PRs that have been approved by product. This is usually applied by a PM.
- `do-not-merge`: PRs that should not be merged.
""",
        )
        prs_needing_approval_df = action_items["prs_needing_approval"]
        if prs_needing_approval_df.empty:
            st.caption("Nothing to show right now.")
        else:
            st.dataframe(
                prs_needing_approval_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Title": st.column_config.TextColumn("Title", width="large"),
                    "URL": st.column_config.LinkColumn("URL", display_text="Open"),
                    "Created": st.column_config.DatetimeColumn("Created", format="distance"),
                    "Labels": st.column_config.ListColumn("Labels"),
                },
            )

        st.subheader(
            "Community PRs ready for review",
            help="""
Lists community PRs that are ready for technical review. These PRs meet all the criteria:
- Not in draft state
- No "[WIP]" in the title
- Has both `change:*` and `impact:*` labels
- No blocking labels (`do-not-merge`, `status:needs-product-approval`, `status:awaiting-user-response`)

This view is informational only - no action is required. It is shown for visibility into existing open community PRs.
""",
        )
        community_prs_ready_df = action_items["community_prs_ready_for_review"]
        if community_prs_ready_df.empty:
            st.caption("Nothing to show right now.")
        else:
            st.dataframe(
                community_prs_ready_df,
                width="stretch",
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


# Main app
st.title(":material/stethoscope: Interrupt rotation")
st.caption("This dashboard provides an overview of repository health and areas that require attention.")

timeframe = st.sidebar.selectbox(
    "Select timeframe",
    ("Last 7 days", "Last 14 days"),
    index=0,
)
if st.sidebar.button(":material/refresh: Refresh data", width="stretch"):
    clear_interrupt_caches()

days = 14 if timeframe == "Last 14 days" else 7
since = date.today() - timedelta(days=days)

# All slow sections are `parallel=True` fragments dispatched here. During a full
# rerun they run concurrently in the coordinator thread pool, so the issue/PR
# snapshot, CI-artifact downloads, flaky-test annotations, unit-test annotations,
# Dependabot alerts, and monitored-repo PR fetches overlap instead of running one
# after another on the main thread.
render_ci_metrics(since)

with st.expander("Helpful processes", icon=":material/menu_book:"):
    st.markdown("""
    - [Issues on Community Cloud](https://www.notion.so/snowflake-corp/Streamlit-OS-Issues-Community-Cloud-dfa2c315cafd434081166f33077c3eb2)
    - [Evaluating Memory Leaks in Streamlit](https://www.notion.so/snowflake-corp/Evaluating-Memory-Leaks-in-Streamlit-2af7170bb41680ed8634dbd5ee414f57)
    """)

st.header(":material/checklist: Action required")

render_issue_action_items(since)

render_flaky_tests(since)

render_ci_test_annotations()

render_dependabot_alerts()

render_monitored_repo_prs()

st.header(":material/visibility: For reference")
st.caption("Informational views only. No action is required from the person on Interrupt.")
with st.expander("Show reference views", expanded=False):
    st.markdown(
        "[![OSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/streamlit/streamlit"
        "?label=openssf+scorecard&style=flat)](https://scorecard.dev/viewer/?uri=github.com/streamlit/streamlit) "
        "[![Socket.dev Rating](https://badge.socket.dev/pypi/package/streamlit)]"
        "(https://socket.dev/pypi/package/streamlit) "
        "[![Spectra Assure Community Badge](https://secure.software/pypi/badge/streamlit)]"
        "(https://secure.software/pypi/packages/streamlit) "
        "[![Libraries.io dependency status for latest release]"
        "(https://img.shields.io/librariesio/release/pypi/streamlit)]"
        "(https://libraries.io/pypi/streamlit) "
        "[![Libraries.io SourceRank](https://img.shields.io/librariesio/sourcerank/pypi/streamlit)]"
        "(https://libraries.io/pypi/streamlit) "
        "[![Snyk Monitoring](https://snyk.io/test/github/streamlit/streamlit/badge.svg)]"
        "(https://security.snyk.io/package/pip/streamlit)"
    )
    render_confirmed_bugs_without_repro(since)

    render_reported_bugs(since)

    render_community_pr_action_items(since)
