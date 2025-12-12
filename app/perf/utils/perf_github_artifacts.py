from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from app.utils.github_utils import download_artifact as download_artifact_bytes
from app.utils.github_utils import get_headers, iter_json_from_zip_bytes


def append_to_performance_scores(
    performance_scores: Dict[str, Dict[str, float]],
    timestamp: str,
    app_name: str,
    score: float,
) -> None:
    if timestamp not in performance_scores:
        performance_scores[timestamp] = {}
    performance_scores[timestamp][app_name] = score


def process_artifact(
    performance_scores: Dict[str, Dict[str, float]],
    artifact: Dict[str, Any],
) -> Dict[str, Dict[str, float]]:
    """
    Process a Lighthouse artifact in-memory (no filesystem extraction).
    """
    archive_url = artifact["archive_download_url"]
    content = download_artifact_bytes(archive_url)
    if content is None:
        raise RuntimeError(f"Failed to download artifact: {artifact.get('name')}")

    timestamp = artifact.get("created_at") or ""
    for member_name, payload in iter_json_from_zip_bytes(content):
        if not isinstance(payload, dict):
            continue
        try:
            score = payload["categories"]["performance"]["score"]
        except Exception:
            continue

        parts = member_name.split("_-_")
        if len(parts) >= 3:
            app_name = parts[1]
            device_type = parts[2]
            key = f"{app_name}_{device_type}"
        else:
            key = member_name

        append_to_performance_scores(performance_scores, timestamp, key, float(score))

    return performance_scores


def get_commit_hashes_for_branch_name(
    branch_name: str,
    limit: int = 50,
    until_date: Optional[str] = None,
) -> List[str]:
    """
    Get the commit hashes for a specific branch name.
    """
    url = "https://api.github.com/repos/streamlit/streamlit/commits"
    params: Dict[str, Any] = {"sha": branch_name, "per_page": limit}
    if until_date:
        params["until"] = f"{until_date}T23:59:59Z"

    response = requests.get(url, headers=get_headers(), params=params, timeout=30)
    response.raise_for_status()
    commits = response.json()
    return [commit["sha"] for commit in commits]


def get_check_run_by_name(
    workflow_runs: List[Dict[str, Any]], name: str
) -> Optional[Dict[str, Any]]:
    return next((run for run in workflow_runs if run["name"] == name), None)


def get_shortest_check_run_by_name(
    workflow_runs: List[Dict[str, Any]], name: str
) -> Optional[Dict[str, Any]]:
    shortest_check_run = None
    shortest_duration = float("inf")

    for check_run in workflow_runs:
        if check_run["name"] == name and check_run["status"] == "completed":
            started_at = datetime.strptime(check_run["started_at"], "%Y-%m-%dT%H:%M:%SZ")
            completed_at = datetime.strptime(
                check_run["completed_at"], "%Y-%m-%dT%H:%M:%SZ"
            )
            duration = (completed_at - started_at).total_seconds()
            if duration < shortest_duration:
                shortest_duration = duration
                shortest_check_run = check_run

    return shortest_check_run


def get_build_from_github(commit_hash: str) -> Optional[Dict[str, Any]]:
    """
    Get workflow runs from GitHub for a specific commit hash.
    Returns a simplified structure expected by perf pages.
    """
    try:
        url = "https://api.github.com/repos/streamlit/streamlit/actions/runs"
        params = {"head_sha": commit_hash}
        response = requests.get(url, headers=get_headers(), params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()

        workflow_runs = payload.get("workflow_runs", [])
        return {
            "status": "completed" if workflow_runs else "not_found",
            "workflow_runs": [
                {
                    "name": run["name"],
                    "status": run["status"],
                    "started_at": run.get("run_started_at") or run.get("created_at"),
                    "completed_at": run.get("updated_at"),
                    "details_url": run["html_url"],
                }
                for run in workflow_runs
            ],
        }
    except Exception:
        return None


def get_playwright_performance_artifact(
    build_data: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    performance_run = get_check_run_by_name(build_data["workflow_runs"], "Performance Suite")

    # NOTE: As of 1/17/2025 we have a single Performance suite in CI. Before
    # this, we had a few other scattered job names. Keep these for legacy.
    if not performance_run:
        performance_run = get_check_run_by_name(
            build_data["workflow_runs"], "playwright-performance"
        )

    if not performance_run:
        performance_run = get_shortest_check_run_by_name(
            build_data["workflow_runs"], "playwright-e2e-tests"
        )

    if not performance_run:
        print("Error finding performance check run")
        return None

    return performance_run


def get_workflow_run_id(ref: str, workflow_name: str) -> Optional[int]:
    """
    Get the workflow run ID for a specific branch and workflow display name.
    This intentionally matches the prior perf behavior (filtering Actions runs by
    branch + name) while using shared auth headers from `app.utils.github_utils`.
    """
    url = "https://api.github.com/repos/streamlit/streamlit/actions/runs"
    params = {"event": "pull_request", "branch": ref}
    response = requests.get(url, headers=get_headers(), params=params, timeout=30)
    response.raise_for_status()
    workflow_runs = response.json().get("workflow_runs", [])
    for run in workflow_runs:
        if run.get("name") == workflow_name:
            return run.get("id")
    return None


def extract_run_id_from_url(url: str) -> Optional[str]:
    match = re.search(r"/runs/(\d+)", url)
    return match.group(1) if match else None


def get_artifact_by_name(
    artifacts: List[Dict[str, Any]], name: str, starts_with: bool = False
) -> Optional[Dict[str, Any]]:
    if starts_with:
        return next((a for a in artifacts if a["name"].startswith(name)), None)
    return next((a for a in artifacts if a["name"] == name), None)

