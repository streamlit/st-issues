from __future__ import annotations

from calendar import monthrange
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Any, Final

import requests
import streamlit as st

from app.utils.github_utils import get_headers

GITHUB_REPO: Final[str] = "streamlit/streamlit"
WORKFLOW_RUNS_URL: Final[str] = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{{workflow_name}}/runs"

# File name in .github/workflows → display name from the workflow `name:` field.
AI_WORKFLOWS: Final[tuple[tuple[str, str], ...]] = (
    ("ai-pr-review.yml", "AI PR Review"),
    ("ai-qa-testing.yml", "AI QA Testing"),
    ("ai-issue-triage.yml", "AI Issue Triage"),
)

WORKFLOW_LABELS: Final[tuple[str, ...]] = tuple(label for _, label in AI_WORKFLOWS)

WORKFLOW_ACTION_URLS: Final[dict[str, str]] = {
    "AI PR Review": f"https://github.com/{GITHUB_REPO}/actions/workflows/ai-pr-review.yml",
    "AI QA Testing": f"https://github.com/{GITHUB_REPO}/actions/workflows/ai-qa-testing.yml",
    "AI Issue Triage": f"https://github.com/{GITHUB_REPO}/actions/workflows/ai-issue-triage.yml",
}

# GitHub's `status` filter also accepts conclusion values. Skip `skipped` on
# purpose: these workflows start on every label event and skip when the label
# is not an AI trigger, which would drown out real usage.
USAGE_STATUSES: Final[tuple[str, ...]] = (
    "success",
    "failure",
    "cancelled",
    "startup_failure",
    "timed_out",
)

OUTCOME_SUCCEEDED: Final[str] = "Succeeded"
OUTCOME_FAILED: Final[str] = "Failed"
OUTCOME_CANCELLED: Final[str] = "Cancelled"
OUTCOME_IN_PROGRESS: Final[str] = "In progress"

FAILED_CONCLUSIONS: Final[frozenset[str]] = frozenset({"failure", "startup_failure", "timed_out"})

TRIGGER_LABELS: Final[dict[str, str]] = {
    "pull_request": "PR label",
    "issues": "Issue label",
    "workflow_dispatch": "Manual",
}

_PER_PAGE: Final[int] = 100
# GitHub caps each listing query at 1,000 runs. Monthly `created` windows stay
# under that cap and keep recent runs from being dropped.
_MAX_PAGES_PER_MONTH: Final[int] = 10
_LOOKBACK_MONTHS: Final[int] = 18
_REQUEST_TIMEOUT_SECONDS: Final[int] = 30
_FETCH_WORKERS: Final[int] = 5


def normalize_conclusion(conclusion: str | None) -> str:
    """Map a GitHub Actions conclusion to a dashboard outcome label."""
    if conclusion == "success":
        return OUTCOME_SUCCEEDED
    if conclusion in FAILED_CONCLUSIONS:
        return OUTCOME_FAILED
    if conclusion == "cancelled":
        return OUTCOME_CANCELLED
    if conclusion is None:
        return OUTCOME_IN_PROGRESS
    return conclusion.replace("_", " ").capitalize()


def trigger_label(event: str | None) -> str:
    """Human-readable trigger for a workflow event name."""
    if not event:
        return "Unknown"
    return TRIGGER_LABELS.get(event, event.replace("_", " ").capitalize())


def _summarize_run(run: dict[str, Any], workflow_label: str) -> dict[str, Any]:
    """Keep the cached payload small and stable for the dashboard."""
    pull_requests = run.get("pull_requests") or []
    first_pr = pull_requests[0] if pull_requests else None
    pr_number = first_pr.get("number") if isinstance(first_pr, dict) else None
    triggering_actor = run.get("triggering_actor") or {}
    actor_login = triggering_actor.get("login") if isinstance(triggering_actor, dict) else None

    return {
        "id": run.get("id"),
        "workflow": workflow_label,
        "event": run.get("event"),
        "conclusion": run.get("conclusion"),
        "outcome": normalize_conclusion(run.get("conclusion")),
        "created_at": run.get("created_at"),
        "run_started_at": run.get("run_started_at"),
        "updated_at": run.get("updated_at"),
        "display_title": run.get("display_title") or "",
        "html_url": run.get("html_url"),
        "run_number": run.get("run_number"),
        "actor": actor_login,
        "head_branch": run.get("head_branch"),
        "pr_number": pr_number,
        "trigger": trigger_label(run.get("event")),
    }


def _month_ranges(num_months: int) -> tuple[tuple[str, str], ...]:
    """Return inclusive YYYY-MM-DD ranges for the last months, newest first."""
    year = date.today().year
    month = date.today().month
    ranges: list[tuple[str, str]] = []
    for _ in range(num_months):
        start = date(year, month, 1)
        end = date(year, month, monthrange(year, month)[1])
        ranges.append((start.isoformat(), end.isoformat()))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return tuple(ranges)


def _fetch_runs_page(
    workflow_name: str,
    status: str,
    page: int,
    headers: dict[str, str],
    created_range: str | None,
) -> tuple[list[dict[str, Any]], str | None]:
    params: dict[str, Any] = {
        "per_page": _PER_PAGE,
        "page": page,
        "status": status,
    }
    if created_range:
        params["created"] = created_range

    try:
        response = requests.get(
            WORKFLOW_RUNS_URL.format(workflow_name=workflow_name),
            headers=headers,
            params=params,
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        return [], f"Request failed for {workflow_name} ({status}): {exc!s}"

    if response.status_code != 200:
        return [], f"GitHub returned {response.status_code} for {workflow_name} ({status}): {response.text[:200]}"

    try:
        payload = response.json()
    except ValueError as exc:
        return [], f"Failed to decode JSON for {workflow_name} ({status}): {exc!s}"

    runs = payload.get("workflow_runs") if isinstance(payload, dict) else None
    if not isinstance(runs, list):
        return [], f"Unexpected workflow run payload for {workflow_name} ({status})"
    return runs, None


def _fetch_runs_for_created_range(
    workflow_name: str,
    status: str,
    headers: dict[str, str],
    created_range: str | None,
) -> tuple[list[dict[str, Any]], str | None]:
    all_runs: list[dict[str, Any]] = []
    for page in range(1, _MAX_PAGES_PER_MONTH + 1):
        runs, error = _fetch_runs_page(workflow_name, status, page, headers, created_range)
        if error:
            return all_runs, error
        if not runs:
            break
        all_runs.extend(runs)
        if len(runs) < _PER_PAGE:
            break
    return all_runs, None


def _fetch_runs_for_status(
    workflow_name: str,
    workflow_label: str,
    status: str,
    headers: dict[str, str],
) -> tuple[list[dict[str, Any]], str | None]:
    """Fetch runs for one workflow/status using monthly created windows."""
    probe_runs, probe_error = _fetch_runs_page(workflow_name, status, 1, headers, None)
    if probe_error:
        return [], probe_error
    if not probe_runs:
        return [], None

    summarized: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    last_error: str | None = None
    month_jobs = _month_ranges(_LOOKBACK_MONTHS)

    with ThreadPoolExecutor(max_workers=_FETCH_WORKERS) as executor:
        futures = [
            executor.submit(
                _fetch_runs_for_created_range,
                workflow_name,
                status,
                headers,
                f"{start}..{end}",
            )
            for start, end in month_jobs
        ]
        for future in as_completed(futures):
            month_runs, error = future.result()
            if error:
                last_error = error
                continue
            for run in month_runs:
                run_id = run.get("id")
                if not isinstance(run_id, int) or run_id in seen_ids:
                    continue
                seen_ids.add(run_id)
                summarized.append(_summarize_run(run, workflow_label))

    return summarized, last_error


@st.cache_data(ttl=60 * 60 * 6, show_spinner="Fetching AI workflow runs...", refresh_mode="background")
def fetch_ai_workflow_runs() -> tuple[list[dict[str, Any]], list[str]]:
    """Fetch completed AI PR review, QA, and issue-triage workflow runs."""
    headers = get_headers()
    jobs = [
        (workflow_file, workflow_label, status)
        for workflow_file, workflow_label in AI_WORKFLOWS
        for status in USAGE_STATUSES
    ]

    all_runs: list[dict[str, Any]] = []
    errors: list[str] = []

    with ThreadPoolExecutor(max_workers=_FETCH_WORKERS) as executor:
        futures = [
            executor.submit(_fetch_runs_for_status, workflow_file, workflow_label, status, headers)
            for workflow_file, workflow_label, status in jobs
        ]
        for future in as_completed(futures):
            runs, error = future.result()
            all_runs.extend(runs)
            if error:
                errors.append(error)

    all_runs.sort(key=lambda run: str(run.get("created_at") or ""), reverse=True)
    return all_runs, errors
