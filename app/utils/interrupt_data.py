"""
Data fetching functions for the interrupt rotation dashboard.
Contains all GitHub-specific business logic for analyzing issues, PRs, and CI metrics.
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter
from datetime import date, datetime, timedelta
from io import BytesIO
from typing import Tuple
from zipfile import ZipFile

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

# Path to the issues folder
DEFAULT_ISSUES_FOLDER = "issues"
PATH_OF_SCRIPT = pathlib.Path(__file__).parent.parent.resolve()
PATH_TO_ISSUES = (
    pathlib.Path(PATH_OF_SCRIPT).parent.joinpath(DEFAULT_ISSUES_FOLDER).resolve()
)


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


@st.cache_data(
    ttl=60 * 60 * 6, show_spinner="Fetching bundle size metrics..."
)  # cache for 6 hours
def get_bundle_size_metrics(since_date: date) -> Tuple[int, int, int, int]:
    """
    Get the total and entry gzip size and the change over a period.
    Returns: (total_gzip, total_gzip_change, entry_gzip, entry_gzip_change)
    """
    runs_in_period = fetch_workflow_runs("pr-preview.yml", since=since_date)

    def get_sizes(run_id: int) -> Tuple[int, int]:
        artifacts = fetch_artifacts(run_id)
        artifact = next(
            (a for a in artifacts if a["name"] == "bundle_analysis_json"), None
        )

        if not artifact:
            return 0, 0

        content = download_artifact(artifact["archive_download_url"])
        if not content:
            return 0, 0

        try:
            with ZipFile(BytesIO(content)) as z:
                for name in z.namelist():
                    if name.endswith(".json"):
                        with z.open(name) as f:
                            bundle_data = json.load(f)
                            total_gzip = 0
                            entry_gzip = 0

                            for item in bundle_data:
                                total_gzip += item.get("gzipSize", 0)
                                if item.get("isEntry"):
                                    entry_gzip += item.get("gzipSize", 0)

                            return total_gzip, entry_gzip
        except Exception:
            return 0, 0

        return 0, 0

    if not runs_in_period:
        # If there are no runs in the selected period, just get the latest one
        latest_run = fetch_workflow_runs("pr-preview.yml", limit=1)
        if not latest_run:
            return 0, 0, 0, 0
        latest_total, latest_entry = get_sizes(latest_run[0]["id"])
        return latest_total, 0, latest_entry, 0

    latest_total, latest_entry = get_sizes(runs_in_period[0]["id"])

    if len(runs_in_period) < 2:
        return latest_total, 0, latest_entry, 0

    oldest_total, oldest_entry = get_sizes(runs_in_period[-1]["id"])

    return (
        latest_total,
        latest_total - oldest_total,
        latest_entry,
        latest_entry - oldest_entry
    )


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
            waiting_for_team_response.append({
                    "Title": i["title"],
                    "URL": i["html_url"],
                    "Created": i["created_at"],
                    "Author": i["user"]["login"],
                    "Labels": list(labels),
            })

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
