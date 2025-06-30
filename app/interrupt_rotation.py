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
@st.cache_data(ttl=60 * 60 * 6)  # cache for 6 hours
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


@st.cache_data(ttl=60 * 60 * 6)  # cache for 6 hours
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


@st.cache_data(ttl=60 * 60 * 6)  # cache for 6 hours
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
                    "Author": i["user"]["login"],
                    "Created": i["created_at"],
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
                        "Author": i["user"]["login"],
                        "Created": i["created_at"],
                    }
                )
    return pd.DataFrame(unprioritized)


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
                        "Author": i["user"]["login"],
                        "Created": i["created_at"],
                    }
                )
    return pd.DataFrame(bugs_without_repro)


@st.cache_data(ttl=60 * 60 * 6)  # cache for 6 hours
def get_flaky_tests(since_date: date) -> pd.DataFrame:
    """Get flaky tests with >= 5 failures."""
    flaky_tests_counter: Counter[str] = Counter()
    workflow_runs = fetch_workflow_runs(
        "playwright.yml", since=since_date, status="success", branch=None
    )

    for run in workflow_runs:
        check_run_ids = fetch_workflow_runs_ids(run["check_suite_id"])
        for check_run_id in check_run_ids:
            annotations = fetch_workflow_run_annotations(check_run_id)
            for annotation in annotations:
                if annotation["path"].startswith("e2e_playwright/"):
                    test_name = (
                        f"{annotation['path'].replace('e2e_playwright/', '')}::"
                        f"{annotation['message'].splitlines()[0]}"
                    )
                    flaky_tests_counter.update([test_name])

    data = [
        {"Test": test, "Failures": count, "Workflow Run": run["html_url"]}
        for test, count in flaky_tests_counter.items()
        if count >= 5
    ]
    return pd.DataFrame(data)


@st.cache_data(ttl=3600)
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

st.subheader("Issues that need triage")
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

st.subheader("Issues missing feature label")
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

st.subheader("Confirmed bugs without a priority")
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

st.subheader("Flaky tests with ≥ 5 failures")
flaky_tests_df = get_flaky_tests(since)
if flaky_tests_df.empty:
    st.success("Congrats, everything is done here!", icon="🎉")
else:
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
        },
    )
st.divider()

st.subheader(
    "Community PRs missing labels",
    help="Community PRs missing `change:*` and/or `impact:*` label",
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
    help="Community PRs with `change:feature` and `impact:users` labels that don't have a `status:needs-product-approval`, `status:product-approved` or `do-not-merge` label.",
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

st.subheader("Open Dependabot PRs")
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

st.subheader("Issues waiting for team response")
waiting_for_team_response_df = get_issue_waiting_for_team_response()
if waiting_for_team_response_df.empty:
    st.success("Congrats, everything is done here!", icon="🎉")
else:
    st.dataframe(
        waiting_for_team_response_df, use_container_width=True, hide_index=True
    )
st.divider()

st.subheader(
    "Confirmed bugs without a reproducible script",
    help="Confirmed bugs created in the selected timeframe that don't have a reproducible script.",
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
