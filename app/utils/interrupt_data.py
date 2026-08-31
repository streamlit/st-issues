"""Data fetching functions for the interrupt rotation dashboard.

Contains all GitHub-specific business logic for analyzing issues, PRs, and CI metrics.
"""

from __future__ import annotations

import json
import pathlib
import re
from collections import Counter
from datetime import date, datetime, timedelta
from io import BytesIO
from typing import Any
from zipfile import ZipFile

import pandas as pd
import streamlit as st

from app.utils.agent_wiki import fetch_wiki_issue_repros, get_synced_wiki_repo_path
from app.utils.github_utils import (
    download_artifact,
    fetch_artifacts,
    fetch_dependabot_alerts,
    fetch_develop_commit_checks,
    fetch_workflow_run_annotations,
    fetch_workflow_run_jobs,
    fetch_workflow_runs,
    fetch_workflow_runs_ids,
    get_all_github_issues,
    get_all_github_prs,
    is_community_author,
)

# Path to the issues folder
DEFAULT_ISSUES_FOLDER = "issues"
PATH_OF_SCRIPT = pathlib.Path(__file__).parent.parent.resolve()
PATH_TO_ISSUES = pathlib.Path(PATH_OF_SCRIPT).parent.joinpath(DEFAULT_ISSUES_FOLDER).resolve()
STREAMLIT_REPO = "streamlit/streamlit"
GITHUB_ACTIONS_LOGIN = "github-actions[bot]"
BOT_PR_LOGINS = frozenset({"dependabot[bot]", GITHUB_ACTIONS_LOGIN})
MONITORED_INTERRUPT_REPOS: tuple[str, ...] = (
    "streamlit/gallery",
    "streamlit/component-template",
    "streamlit/streamlit-bokeh",
    "streamlit/streamlit-pdf",
    "streamlit/agent-skills",
    "streamlit/st-issues",
)
# Repos that are not fully monitored, but whose Dependabot and GitHub Actions PRs
# should still appear in the important-repos table. Repos already listed in
# MONITORED_INTERRUPT_REPOS are skipped during the extra fetch to avoid duplicates.
BOT_PR_INTERRUPT_REPOS: tuple[str, ...] = (
    "streamlit/docs",
    "streamlit/streamlit-pivot-table",
    "streamlit/streamlit-bokeh",
    "streamlit/streamlit-pdf",
    "streamlit/blank-app-template",
)

# Title prefix of the automated release PRs that bump the version identifiers
# (for example "[chore] Release v1.61.0").
RELEASE_PR_TITLE_PREFIX = "[chore] Release"

# Window used by the interrupt CI-check metric: newest commits on `develop`.
DEVELOP_COMMIT_WINDOW = 10
_FAILED_CHECK_CONCLUSIONS: frozenset[str] = frozenset({"failure", "timed_out", "startup_failure"})
_FAILED_STATUS_STATES: frozenset[str] = frozenset({"failure", "error"})

# Latest successful unit-test jobs whose check-run annotations are tracked as
# interrupt action items (deprecations, resource warnings, tool notices, ...).
PYTHON_TESTS_WORKFLOW = "python-tests.yml"
PYTHON_UNIT_TESTS_MAX_JOB = "py-unit-tests (max)"
JS_TESTS_WORKFLOW = "js-tests.yml"
JS_UNIT_TESTS_JOB = "js-unit-tests"
_ANNOTATION_LEVEL_LABELS: dict[str, str] = {
    "failure": "error",
    "warning": "warning",
    "notice": "notice",
}
_ANNOTATION_LEVEL_SORT: dict[str, int] = {"error": 0, "warning": 1, "notice": 2}
_DEPENDABOT_SEVERITY_SORT: dict[str, int] = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_DEPENDABOT_ALERT_COLUMNS: tuple[str, ...] = (
    "Severity",
    "Package",
    "Ecosystem",
    "Manifest",
    "Summary",
    "Advisory",
    "Patched",
    "Created",
    "URL",
)
_HEX_OBJECT_ID_RE = re.compile(r"0x[0-9a-fA-F]+")
_CI_TEST_ANNOTATION_COLUMNS: tuple[str, ...] = ("Level", "Job", "Message", "Location", "Count", "URL")


def _issue_row(issue: dict[str, Any], labels: set[str]) -> dict[str, Any]:
    return {
        "Title": issue["title"],
        "URL": issue["html_url"],
        "Created": issue["created_at"],
        "Author": issue["user"]["login"],
        "Labels": list(labels),
    }


def _is_streamlit_repo_pr(pr: dict[str, Any]) -> bool:
    return f"github.com/{STREAMLIT_REPO}/" in pr.get("html_url", "")


def _pr_row(pr: dict[str, Any], labels: set[str], author: str | None) -> dict[str, Any]:
    return {
        "Title": pr["title"],
        "URL": pr["html_url"],
        "Created": pr["created_at"],
        "Author": author,
        "Labels": list(labels),
    }


def _monitored_pr_row(pr: dict[str, Any], repo: str) -> dict[str, Any]:
    return {
        "Repository": repo,
        "Title": pr["title"],
        "URL": pr["html_url"],
        "Created": pr["created_at"],
        "Updated": pr["updated_at"],
        "Author": pr.get("user", {}).get("login"),
        "Draft": pr.get("draft", False),
    }


@st.cache_data(ttl=60 * 10, max_entries=64, show_spinner=False, refresh_mode="background")
def get_interrupt_data_snapshot() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Fetch the open issue/PR snapshot used by the Interrupt Rotation page."""
    issues = get_all_github_issues(state="open")
    prs = get_all_github_prs(state="open", repo=STREAMLIT_REPO)
    return issues, prs


@st.cache_data(ttl=60 * 10, max_entries=64, show_spinner=False, refresh_mode="background")
def get_monitored_repo_open_prs() -> pd.DataFrame:
    """Fetch open PRs from Streamlit-managed repos that the interrupt rotation should monitor.

    Includes every open PR in `MONITORED_INTERRUPT_REPOS`, plus Dependabot and GitHub Actions
    PRs from `BOT_PR_INTERRUPT_REPOS` (repos already fully monitored are not fetched twice).
    """
    rows: list[dict[str, Any]] = []
    fetched_repos: set[str] = set()

    for repo in MONITORED_INTERRUPT_REPOS:
        repo_prs = get_all_github_prs(state="open", repo=repo)
        rows.extend(_monitored_pr_row(pr, repo) for pr in repo_prs)
        fetched_repos.add(repo)

    for repo in BOT_PR_INTERRUPT_REPOS:
        if repo in fetched_repos:
            continue
        repo_prs = get_all_github_prs(state="open", repo=repo)
        rows.extend(_monitored_pr_row(pr, repo) for pr in repo_prs if pr.get("user", {}).get("login") in BOT_PR_LOGINS)
        fetched_repos.add(repo)

    monitored_prs = pd.DataFrame(rows)
    if monitored_prs.empty:
        return monitored_prs

    return monitored_prs.sort_values(
        by=["Updated", "Created", "Repository", "Title"],
        ascending=[False, False, True, True],
    ).reset_index(drop=True)


def _build_interrupt_action_items(
    issues: list[dict[str, Any]],
    prs: list[dict[str, Any]],
    since_date: date,
) -> dict[str, pd.DataFrame]:
    needs_triage: list[dict[str, Any]] = []
    missing_label_issues: list[dict[str, Any]] = []
    waiting_for_team_response: list[dict[str, Any]] = []
    unprioritized: list[dict[str, Any]] = []
    high_priority_bugs: list[dict[str, Any]] = []
    bugs_without_repro: list[dict[str, Any]] = []
    missing_label_prs: list[dict[str, Any]] = []
    needs_approval_prs: list[dict[str, Any]] = []
    ready_for_review: list[dict[str, Any]] = []
    bot_prs: list[dict[str, Any]] = []
    release_prs: list[dict[str, Any]] = []

    for issue in issues:
        if "pull_request" in issue:
            continue

        labels = {label["name"] for label in issue["labels"]}
        issue_common = _issue_row(issue, labels)

        if "status:needs-triage" in labels:
            needs_triage.append(
                {
                    "Title": issue_common["Title"],
                    "URL": issue_common["URL"],
                    "Author": issue_common["Author"],
                    "Created": issue_common["Created"],
                }
            )

        if not any(label.startswith(("feature:", "area:")) or label == "type:kudos" for label in labels):
            missing_label_issues.append(issue_common)

        if "status:awaiting-team-response" in labels:
            waiting_for_team_response.append(issue_common)

        if "type:bug" in labels and "status:confirmed" in labels:
            has_priority = any(label.startswith("priority:P") for label in labels)
            if not has_priority:
                unprioritized.append(
                    {
                        "Title": issue_common["Title"],
                        "URL": issue_common["URL"],
                        "Created": issue_common["Created"],
                        "Author": issue_common["Author"],
                    }
                )

            if any(label in {"priority:P0", "priority:P1", "priority:P2"} for label in labels):
                priority = next((label for label in labels if label.startswith("priority:P")), "Unknown")
                high_priority_bugs.append(
                    {
                        "Title": issue_common["Title"],
                        "URL": issue_common["URL"],
                        "Created": issue_common["Created"],
                        "Assignees": [assignee["login"] for assignee in issue.get("assignees", [])],
                        "Priority": priority,
                        "Labels": issue_common["Labels"],
                        "Author": issue_common["Author"],
                    }
                )

            # Multipage app bugs are not easy to reproduce in the issues app.
            if "feature:multipage-apps" not in labels:
                created_at = datetime.fromisoformat(issue["created_at"]).date()
                if created_at >= since_date and not get_reproducible_example_exists(issue["number"]):
                    bugs_without_repro.append(
                        {
                            "Title": issue_common["Title"],
                            "URL": issue_common["URL"],
                            "Created": issue_common["Created"],
                            "Author": issue_common["Author"],
                        }
                    )

    for pr in prs:
        author = pr.get("user", {}).get("login")
        labels = {label["name"] for label in pr["labels"]}

        # Mirrors the GitHub search `is:pr "[chore] Release" author:app/github-actions is:open`,
        # where `app/github-actions` is the `github-actions[bot]` login in the REST payload.
        is_release_pr = (
            author == GITHUB_ACTIONS_LOGIN
            and pr["title"].startswith(RELEASE_PR_TITLE_PREFIX)
            and _is_streamlit_repo_pr(pr)
        )
        if is_release_pr:
            release_prs.append(
                {
                    "Title": pr["title"],
                    "URL": pr["html_url"],
                    "Created": pr["created_at"],
                }
            )
        elif author and author.endswith("[bot]") and "do-not-merge" not in labels and _is_streamlit_repo_pr(pr):
            # Dependabot, github-actions, and other bots from streamlit/streamlit only.
            # Release PRs are listed separately above; docs bot PRs are in important repos.
            bot_prs.append(
                {
                    "Title": pr["title"],
                    "URL": pr["html_url"],
                    "Created": pr["created_at"],
                    "Author": author,
                }
            )

        if not author or not is_community_author(author):
            continue

        pr_common = _pr_row(pr, labels, author)
        has_change = any(label.startswith("change:") for label in labels)
        has_impact = any(label.startswith("impact:") for label in labels)

        if not has_change or not has_impact:
            missing_label_prs.append(pr_common)

        has_required_labels = "change:feature" in labels and "impact:users" in labels
        has_status_labels = (
            "status:needs-product-approval" in labels or "status:product-approved" in labels or "do-not-merge" in labels
        )
        if has_required_labels and not has_status_labels:
            needs_approval_prs.append(pr_common)

        if pr.get("draft", False):
            continue
        if "[WIP]" in pr.get("title", "").upper():
            continue
        blocking_labels = {
            "do-not-merge",
            "status:needs-product-approval",
            "status:awaiting-user-response",
        }
        if any(label in blocking_labels for label in labels):
            continue
        if not has_change or not has_impact:
            continue

        ready_for_review.append(
            {
                "Title": pr_common["Title"],
                "URL": pr_common["URL"],
                "Assignees": [assignee["login"] for assignee in pr.get("assignees", [])],
                "Created": pr_common["Created"],
                "Updated": pr["updated_at"],
                "Labels": pr_common["Labels"],
                "Author": author,
            }
        )

    return {
        "needs_triage": pd.DataFrame(needs_triage),
        "missing_labels_issues": pd.DataFrame(missing_label_issues),
        "waiting_for_team_response": pd.DataFrame(waiting_for_team_response),
        "unprioritized_bugs": pd.DataFrame(unprioritized),
        "high_priority_bugs": pd.DataFrame(high_priority_bugs),
        "missing_labels_prs": pd.DataFrame(missing_label_prs),
        "prs_needing_approval": pd.DataFrame(needs_approval_prs),
        "open_bot_prs": pd.DataFrame(bot_prs),
        "open_release_prs": pd.DataFrame(release_prs),
        "community_prs_ready_for_review": pd.DataFrame(ready_for_review),
        "confirmed_bugs_without_repro": pd.DataFrame(bugs_without_repro),
    }


@st.cache_data(ttl=60 * 5, max_entries=64, show_spinner=False, refresh_mode="background")
def build_interrupt_action_items(since_date: date) -> dict[str, pd.DataFrame]:
    """Build all interrupt action-item tables from a shared issue/PR snapshot."""
    issues, prs = get_interrupt_data_snapshot()
    return _build_interrupt_action_items(issues=issues, prs=prs, since_date=since_date)


@st.cache_data(
    ttl=60 * 60 * 6, show_spinner="Fetching python test coverage...", refresh_mode="background"
)  # cache for 6 hours
def get_python_test_coverage_metrics(since_date: date) -> tuple[float, float]:
    """Get the python test coverage and the change over a period."""
    runs_in_period = fetch_workflow_runs("python-tests.yml", since=since_date)

    def get_coverage(run_id: int) -> float:
        artifacts = fetch_artifacts(run_id)
        artifact = next((a for a in artifacts if a["name"] == "combined_coverage_json"), None)
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
    ttl=60 * 60 * 6, show_spinner="Fetching frontend test coverage...", refresh_mode="background"
)  # cache for 6 hours
def get_frontend_test_coverage_metrics(since_date: date) -> tuple[float, float]:
    """Get the frontend test coverage and the change over a period."""
    runs_in_period = fetch_workflow_runs("js-tests.yml", since=since_date)

    def get_coverage(run_id: int) -> float:
        artifacts = fetch_artifacts(run_id)
        artifact = next((a for a in artifacts if a["name"] == "vitest_coverage_json"), None)
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


@st.cache_data(ttl=60 * 60 * 6, show_spinner="Fetching wheel size...", refresh_mode="background")  # cache for 6 hours
def get_wheel_size_metrics(since_date: date) -> tuple[int, int]:
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
    ttl=60 * 60 * 6, show_spinner="Fetching bundle size metrics...", refresh_mode="background"
)  # cache for 6 hours
def get_bundle_size_metrics(since_date: date) -> tuple[int, int, int, int]:
    """Get the total and entry gzip size and the change over a period.

    Returns: (total_gzip, total_gzip_change, entry_gzip, entry_gzip_change).
    """
    runs_in_period = fetch_workflow_runs("pr-preview.yml", since=since_date)

    def get_sizes(run_id: int) -> tuple[int, int]:
        artifacts = fetch_artifacts(run_id)
        artifact = next((a for a in artifacts if a["name"] == "bundle_analysis_json"), None)

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
        latest_entry - oldest_entry,
    )


@st.cache_data(ttl=60 * 60 * 6, max_entries=64, show_spinner=False, refresh_mode="background")
def _load_playwright_test_stats(run_id: int) -> dict[str, Any] | None:
    """Download and parse the Playwright test-stats JSON for a workflow run."""
    artifacts = fetch_artifacts(run_id)
    artifact = next((a for a in artifacts if a["name"].startswith("playwright_test_stats")), None)
    if not artifact:
        return None
    content = download_artifact(artifact["archive_download_url"])
    if not content:
        return None
    try:
        with ZipFile(BytesIO(content)) as z:
            for name in z.namelist():
                if name.endswith(".json"):
                    with z.open(name) as f:
                        data = json.load(f)
                        return data if isinstance(data, dict) else None
    except Exception:
        return None
    return None


def _check_failed(check: dict[str, Any]) -> bool | None:
    """Return True if the check failed, False if it passed, None if it should be ignored."""
    kind = check.get("kind")
    if kind == "check_run":
        if check.get("status") != "completed":
            return None
        conclusion = check.get("conclusion")
        if conclusion in _FAILED_CHECK_CONCLUSIONS:
            return True
        if conclusion == "success":
            return False
        return None
    if kind == "status":
        state = check.get("state")
        if state in _FAILED_STATUS_STATES:
            return True
        if state == "success":
            return False
        return None
    return None


def _compute_ci_failed_check_metrics(
    commits: list[dict[str, Any]],
) -> tuple[float, int, int]:
    """Compute the failed-check rate across GitHub checks on the given commits.

    `commits` is newest-first. Returns (percentage, failing_check_count, total_check_count).
    """
    failing = 0
    total = 0
    for commit in commits:
        for check in commit.get("checks") or []:
            outcome = _check_failed(check)
            if outcome is None:
                continue
            total += 1
            if outcome:
                failing += 1

    if total == 0:
        return 0.0, 0, 0
    return 100.0 * failing / total, failing, total


@st.cache_data(
    ttl=60 * 60 * 6, show_spinner="Fetching failed CI checks...", refresh_mode="background"
)  # cache for 6 hours
def get_ci_failing_test_run_metrics(_result_version: int = 2) -> tuple[float, int, int]:
    """Get the share of GitHub checks that failed on recent develop commits.

    Looks at every CheckRun and commit status on the last `DEVELOP_COMMIT_WINDOW`
    commits to `develop`.
    """
    _ = _result_version  # Cache-key bump after the return value dropped the sparkline list.
    commits = fetch_develop_commit_checks(limit=DEVELOP_COMMIT_WINDOW)
    return _compute_ci_failed_check_metrics(commits)


@st.cache_data(
    ttl=60 * 60 * 6, show_spinner="Fetching Playwright test count...", refresh_mode="background"
)  # cache for 6 hours
def get_playwright_test_count_metrics(since_date: date) -> tuple[int, int]:
    """Get the Playwright E2E test count and the change over a period."""
    runs_in_period = fetch_workflow_runs("playwright.yml", since=since_date)

    def get_test_count(run_id: int) -> int:
        data = _load_playwright_test_stats(run_id)
        if not data:
            return 0
        return int(data.get("summary", {}).get("total_tests", 0) or 0)

    if not runs_in_period:
        latest_run = fetch_workflow_runs("playwright.yml", limit=1)
        if not latest_run:
            return 0, 0
        latest_count = get_test_count(latest_run[0]["id"])
        return latest_count, 0

    latest_count = get_test_count(runs_in_period[0]["id"])

    if len(runs_in_period) < 2:
        return latest_count, 0

    oldest_count = get_test_count(runs_in_period[-1]["id"])

    return latest_count, latest_count - oldest_count


def get_bug_metrics(since_date: date) -> tuple[int, int]:
    """Get the total number of open bugs and closed bugs in the period.

    Returns:
        Tuple of (open_bug_count, closed_bugs_in_period)
    """
    all_issues = get_all_github_issues(state="all")
    open_bugs = 0
    closed_bugs_in_period = 0

    for i in all_issues:
        if "pull_request" in i:
            continue
        labels = {label["name"] for label in i["labels"]}
        if "type:bug" not in labels:
            continue

        if i["state"] == "open":
            open_bugs += 1
        elif i.get("closed_at"):
            closed_at = datetime.fromisoformat(i["closed_at"])
            if closed_at.date() >= since_date:
                closed_bugs_in_period += 1

    return open_bugs, closed_bugs_in_period


@st.cache_data(ttl=60 * 10, max_entries=64, show_spinner=False, refresh_mode="background")
def get_reported_bugs(since_date: date) -> pd.DataFrame:
    """Get all bugs (`type:bug`) reported in the given timeframe, regardless of state.

    Includes both open and closed issues, filtered by their creation date.
    """
    all_issues = get_all_github_issues(state="all")

    rows: list[dict[str, Any]] = []
    for issue in all_issues:
        if "pull_request" in issue:
            continue
        labels = {label["name"] for label in issue["labels"]}
        if "type:bug" not in labels:
            continue
        created_at = datetime.fromisoformat(issue["created_at"]).date()
        if created_at < since_date:
            continue
        rows.append(
            {
                "Title": issue["title"],
                "URL": issue["html_url"],
                "State": [issue["state"]],
                "Priority": sorted(label for label in labels if label.startswith("priority:P")),
                "Confirmed": "status:confirmed" in labels,
                "Created": issue["created_at"],
                "Author": issue["user"]["login"],
                "Labels": list(labels),
            }
        )

    reported_bugs = pd.DataFrame(rows)
    if reported_bugs.empty:
        return reported_bugs

    return reported_bugs.sort_values(by="Created", ascending=False).reset_index(drop=True)


def get_reproducible_example_exists(issue_number: int) -> bool:
    """Check if a reproducible example exists for an issue.

    Considers both local reproductions merged into st-issues and reproductions
    published in the agent wiki.
    """
    issue_folder_name = f"gh-{issue_number}"
    if PATH_TO_ISSUES.joinpath(issue_folder_name).is_dir():
        return True

    wiki_repros, _ = fetch_wiki_issue_repros()
    return issue_number in wiki_repros


def get_needs_triage_issues() -> pd.DataFrame:
    """Get issues that need triage."""
    data = build_interrupt_action_items(date.today())
    return data["needs_triage"].copy()


def get_missing_labels_issues() -> pd.DataFrame:
    """Get issues missing feature/area labels."""
    data = build_interrupt_action_items(date.today())
    return data["missing_labels_issues"].copy()


def get_issue_waiting_for_team_response() -> pd.DataFrame:
    """Get issues waiting for team response."""
    data = build_interrupt_action_items(date.today())
    return data["waiting_for_team_response"].copy()


def get_missing_labels_prs() -> pd.DataFrame:
    """Get community PRs missing change/impact labels."""
    data = build_interrupt_action_items(date.today())
    return data["missing_labels_prs"].copy()


def get_prs_needing_product_approval() -> pd.DataFrame:
    """Get community PRs with feature changes that need product approval."""
    data = build_interrupt_action_items(date.today())
    return data["prs_needing_approval"].copy()


def get_community_prs_ready_for_review() -> pd.DataFrame:
    """Get community PRs that are ready for review."""
    data = build_interrupt_action_items(date.today())
    return data["community_prs_ready_for_review"].copy()


def get_unprioritized_bugs() -> pd.DataFrame:
    """Get confirmed bugs without a priority."""
    data = build_interrupt_action_items(date.today())
    return data["unprioritized_bugs"].copy()


def get_high_priority_bugs() -> pd.DataFrame:
    """Get all high-priority (P0, P1, P2) bugs."""
    data = build_interrupt_action_items(date.today())
    return data["high_priority_bugs"].copy()


def get_confirmed_bugs_without_repro_script(since_date: date) -> pd.DataFrame:
    """Get confirmed bugs created since a date that don't have a repro script."""
    data = build_interrupt_action_items(since_date)
    return data["confirmed_bugs_without_repro"].copy()


def _empty_ci_test_annotations_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Level": pd.Series(dtype="string"),
            "Job": pd.Series(dtype="string"),
            "Message": pd.Series(dtype="string"),
            "Location": pd.Series(dtype="string"),
            "Count": pd.Series(dtype="int64"),
            "URL": pd.Series(dtype="string"),
        }
    )


def _annotation_first_line(message: str) -> str:
    return message.strip().split("\n", maxsplit=1)[0]


def _annotation_identity_message(message: str) -> str:
    """Collapse volatile object ids so the same warning is not listed twice."""
    return _HEX_OBJECT_ID_RE.sub("0x…", _annotation_first_line(message))


def _format_annotation_location(path: str, start_line: object) -> str:
    if path and isinstance(start_line, int):
        return f"{path}#L{start_line}"
    return path


def _unique_annotation_rows(
    annotations: list[dict[str, Any]],
    *,
    job_name: str,
    job_url: str,
) -> list[dict[str, Any]]:
    """Deduplicate check-run annotations for a single job."""
    grouped: dict[tuple[object, ...], dict[str, Any]] = {}
    for annotation in annotations:
        if not isinstance(annotation, dict):
            continue
        raw_level = str(annotation.get("annotation_level") or "notice")
        level = _ANNOTATION_LEVEL_LABELS.get(raw_level, raw_level)
        path = str(annotation.get("path") or "")
        start_line = annotation.get("start_line")
        message = str(annotation.get("message") or "")
        identity = (level, job_name, path, start_line, _annotation_identity_message(message))
        existing = grouped.get(identity)
        if existing is not None:
            existing["Count"] += 1
            continue
        grouped[identity] = {
            "Level": level,
            "Job": job_name,
            "Message": _annotation_first_line(message),
            "Location": _format_annotation_location(path, start_line),
            "Count": 1,
            "URL": job_url,
        }
    return list(grouped.values())


def _sort_annotation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            _ANNOTATION_LEVEL_SORT.get(str(row["Level"]), 99),
            str(row["Job"]),
            str(row["Message"]),
        ),
    )


def _annotations_for_latest_job(workflow_name: str, job_name: str) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Load unique annotations from the named job on the latest successful develop run."""
    source = {
        "workflow": workflow_name,
        "job": job_name,
        "job_url": "",
        "run_url": "",
        "created_at": "",
    }
    runs = fetch_workflow_runs(workflow_name, limit=1, status="success", branch="develop")
    if not runs:
        return [], source

    run = runs[0]
    source["run_url"] = str(run.get("html_url") or "")
    source["created_at"] = str(run.get("created_at") or "")
    jobs = fetch_workflow_run_jobs(run["id"])
    job = next((candidate for candidate in jobs if candidate.get("name") == job_name), None)
    if job is None:
        return [], source

    source["job_url"] = str(job.get("html_url") or "")
    annotations = fetch_workflow_run_annotations(job["id"])
    return _unique_annotation_rows(annotations, job_name=job_name, job_url=source["job_url"]), source


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False, refresh_mode="background")  # cache for 6 hours
def get_ci_test_annotations() -> tuple[pd.DataFrame, list[dict[str, str]]]:
    """Unique annotations from the latest successful Python (max) and JS unit-test jobs.

    Uses the last successful `python-tests.yml` / `js-tests.yml` runs on `develop`.
    """
    python_rows, python_source = _annotations_for_latest_job(PYTHON_TESTS_WORKFLOW, PYTHON_UNIT_TESTS_MAX_JOB)
    js_rows, js_source = _annotations_for_latest_job(JS_TESTS_WORKFLOW, JS_UNIT_TESTS_JOB)
    sources = [python_source, js_source]
    rows = _sort_annotation_rows([*python_rows, *js_rows])
    if not rows:
        return _empty_ci_test_annotations_df(), sources
    return pd.DataFrame(rows, columns=list(_CI_TEST_ANNOTATION_COLUMNS)), sources


def _empty_dependabot_alerts_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Severity": pd.Series(dtype="string"),
            "Package": pd.Series(dtype="string"),
            "Ecosystem": pd.Series(dtype="string"),
            "Manifest": pd.Series(dtype="string"),
            "Summary": pd.Series(dtype="string"),
            "Advisory": pd.Series(dtype="string"),
            "Patched": pd.Series(dtype="string"),
            "Created": pd.Series(dtype="string"),
            "URL": pd.Series(dtype="string"),
        }
    )


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dependabot_alert_row(alert: dict[str, Any]) -> dict[str, Any]:
    advisory = _as_dict(alert.get("security_advisory"))
    vulnerability = _as_dict(alert.get("security_vulnerability"))
    dependency = _as_dict(alert.get("dependency"))
    package = _as_dict(dependency.get("package"))
    patched = vulnerability.get("first_patched_version")
    patched_id = ""
    if isinstance(patched, dict):
        patched_id = str(patched.get("identifier") or "")
    cve_id = advisory.get("cve_id")
    ghsa_id = advisory.get("ghsa_id")
    return {
        "Severity": str(advisory.get("severity") or vulnerability.get("severity") or ""),
        "Package": str(package.get("name") or ""),
        "Ecosystem": str(package.get("ecosystem") or ""),
        "Manifest": str(dependency.get("manifest_path") or ""),
        "Summary": str(advisory.get("summary") or ""),
        "Advisory": str(cve_id or ghsa_id or ""),
        "Patched": patched_id,
        "Created": str(alert.get("created_at") or ""),
        "URL": str(alert.get("html_url") or ""),
    }


@st.cache_data(ttl=60 * 15, max_entries=8, show_spinner=False, refresh_mode="background")
def get_dependabot_alerts() -> pd.DataFrame:
    """Open Dependabot alerts for `streamlit/streamlit`."""
    alerts = fetch_dependabot_alerts(STREAMLIT_REPO)
    rows = [_dependabot_alert_row(alert) for alert in alerts if isinstance(alert, dict)]
    if not rows:
        return _empty_dependabot_alerts_df()
    alerts_df = pd.DataFrame(rows, columns=list(_DEPENDABOT_ALERT_COLUMNS))
    alerts_df["_severity_sort"] = alerts_df["Severity"].map(_DEPENDABOT_SEVERITY_SORT).fillna(99)
    return (
        alerts_df.sort_values(by=["_severity_sort", "Created"], ascending=[True, False])
        .drop(columns=["_severity_sort"])
        .reset_index(drop=True)
    )


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False, refresh_mode="background")  # cache for 6 hours
def get_flaky_tests(since_date: date, min_failures: int = 10) -> pd.DataFrame:
    """Get flaky tests with >= min_failures."""
    flaky_tests_counter: Counter[str] = Counter()
    example_run: dict[str, str] = {}
    last_failure_date: dict[str, date] = {}

    workflow_runs = fetch_workflow_runs("playwright.yml", since=since_date, status="success", branch=None, limit=200)

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
                        last_failure_date[test_name] = date.fromisoformat(run["created_at"][:10])

    data = [
        {
            "Test": test,
            "Failures": count,
            "Workflow Run": example_run[test],
            "Last Failure Date": last_failure_date[test],
        }
        for test, count in flaky_tests_counter.items()
        # Should be atleast min_failures and the last failure should be in the last 4 days
        if count >= min_failures and last_failure_date[test] > date.today() - timedelta(days=4)
    ]
    return pd.DataFrame(data)


def get_open_bot_prs() -> pd.DataFrame:
    """Get open bot PRs from `streamlit/streamlit` without 'do-not-merge' label.

    Automated release PRs are excluded; use `get_open_release_prs` for those.
    Dependabot and GitHub Actions PRs from other Streamlit repos appear in the
    important-repos table instead.
    """
    data = build_interrupt_action_items(date.today())
    return data["open_bot_prs"].copy()


def get_open_release_prs() -> pd.DataFrame:
    """Get open automated release PRs that bump the version identifiers."""
    data = build_interrupt_action_items(date.today())
    return data["open_release_prs"].copy()


def clear_interrupt_caches() -> None:
    """Drop interrupt-page caches, including nested GitHub fetches they depend on.

    Call this from the Interrupt Refresh button. Clearing only the page wrappers
    would still return stale workflow runs, issues, and annotations from the
    inner ``@st.cache_data`` helpers.
    """
    page_caches = (
        get_interrupt_data_snapshot,
        get_monitored_repo_open_prs,
        build_interrupt_action_items,
        get_python_test_coverage_metrics,
        get_frontend_test_coverage_metrics,
        get_wheel_size_metrics,
        get_bundle_size_metrics,
        get_ci_failing_test_run_metrics,
        get_playwright_test_count_metrics,
        _load_playwright_test_stats,
        get_reported_bugs,
        get_ci_test_annotations,
        get_dependabot_alerts,
        get_flaky_tests,
    )
    nested_caches = (
        get_all_github_issues,
        get_all_github_prs,
        fetch_dependabot_alerts,
        fetch_develop_commit_checks,
        fetch_workflow_runs,
        fetch_workflow_run_jobs,
        fetch_workflow_run_annotations,
        fetch_workflow_runs_ids,
        fetch_artifacts,
        download_artifact,
        fetch_wiki_issue_repros,
        get_synced_wiki_repo_path,
    )
    for cached in (*page_caches, *nested_caches):
        cached.clear()
