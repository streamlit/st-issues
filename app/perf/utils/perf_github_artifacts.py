from __future__ import annotations

import json
import os
import re
import shutil
import time
import zipfile
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from app.utils.github_utils import download_artifact as download_artifact_bytes
from app.utils.github_utils import fetch_artifacts, get_headers

this_file_directory = os.path.dirname(os.path.realpath(__file__))
artifact_directory = os.path.abspath(os.path.join(this_file_directory, "../../artifacts"))

_DEFAULT_ARTIFACT_PRUNE_DAYS = 7


def _safe_extract_zip(zip_ref: zipfile.ZipFile, extract_to: str) -> None:
    """
    Extract a zip file safely to prevent Zip Slip (path traversal).
    """
    extract_to_real = os.path.realpath(extract_to)
    for member in zip_ref.infolist():
        member_name = member.filename
        # Zip files can contain absolute paths or ".." components.
        if os.path.isabs(member_name):
            raise ValueError(f"Unsafe zip member path (absolute): {member_name}")

        dest_path = os.path.realpath(os.path.join(extract_to_real, member_name))
        if not (dest_path == extract_to_real or dest_path.startswith(extract_to_real + os.sep)):
            raise ValueError(f"Unsafe zip member path (traversal): {member_name}")

    zip_ref.extractall(extract_to)


def prune_artifacts_directory(*, max_age_days: int = _DEFAULT_ARTIFACT_PRUNE_DAYS) -> int:
    """
    Remove artifact subdirectories older than `max_age_days`.

    This directory is treated as a cache. Pruning prevents unbounded growth.

    Returns the number of directories removed.
    """
    if max_age_days <= 0:
        return 0

    if not os.path.exists(artifact_directory):
        return 0

    cutoff = time.time() - (max_age_days * 24 * 60 * 60)
    removed = 0

    # Only prune direct subdirectories to avoid surprises.
    for name in os.listdir(artifact_directory):
        path = os.path.join(artifact_directory, name)
        if not os.path.isdir(path):
            continue

        try:
            mtime = os.path.getmtime(path)
        except OSError:
            continue

        if mtime < cutoff:
            shutil.rmtree(path, ignore_errors=True)
            removed += 1

    return removed


def unzip_file(zip_path: str) -> str:
    """
    Unzip a zip file to a directory in the ./artifacts directory that has the same name as the file.
    """
    file_name = os.path.splitext(os.path.basename(zip_path))[0]
    extract_to = os.path.join(artifact_directory, file_name)
    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        _safe_extract_zip(zip_ref, extract_to)
    return extract_to


def append_to_performance_scores(
    performance_scores: Dict[str, Dict[str, float]],
    timestamp: str,
    app_name: str,
    score: float,
) -> None:
    if timestamp not in performance_scores:
        performance_scores[timestamp] = {}
    performance_scores[timestamp][app_name] = score


def read_json_files(
    performance_scores: Dict[str, Dict[str, float]],
    timestamp: str,
    directory: str,
) -> None:
    """
    Read JSON files from a directory and append their performance scores to the
    performance_scores dictionary.
    """
    for root, _, files in os.walk(directory):
        for file in files:
            if not file.endswith(".json"):
                continue
            json_path = os.path.join(root, file)
            with open(json_path, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
                app_name = json_path.split("_-_")[1]
                device_type = json_path.split("_-_")[2]
                append_to_performance_scores(
                    performance_scores,
                    timestamp,
                    f"{app_name}_{device_type}",
                    data["categories"]["performance"]["score"],
                )


def process_artifact(
    performance_scores: Dict[str, Dict[str, float]],
    artifact: Dict[str, Any],
) -> Dict[str, Dict[str, float]]:
    """
    Process an artifact by downloading, unzipping, and reading its JSON files.
    Uses shared `app.utils.github_utils` for artifact download/auth.
    """
    archive_url = artifact["archive_download_url"]
    artifact_name = artifact["name"]

    content = download_artifact_bytes(archive_url)
    if content is None:
        raise RuntimeError(f"Failed to download artifact: {artifact_name}")

    os.makedirs(artifact_directory, exist_ok=True)
    zip_path = os.path.join(artifact_directory, f"{artifact_name}.zip")
    extracted_dir: str | None = None
    try:
        with open(zip_path, "wb") as f:
            f.write(content)

        extracted_dir = unzip_file(zip_path)
        read_json_files(performance_scores, artifact["created_at"], extracted_dir)
    finally:
        # Best-effort cleanup to avoid unbounded disk usage.
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except OSError:
            pass

        # This helper is used for ad-hoc single-run processing; avoid leaving extracted dirs around.
        if extracted_dir and os.path.exists(extracted_dir):
            shutil.rmtree(extracted_dir, ignore_errors=True)

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


def get_artifact_dir_for_run(run_id: str) -> str:
    return os.path.join(artifact_directory, run_id)


def _write_zip_for_run(run_id: str, content: bytes) -> str:
    os.makedirs(artifact_directory, exist_ok=True)
    # Important: use `run_id` as the zip basename so `unzip_file()` extracts to
    # `<artifact_directory>/<run_id>`, which matches `get_artifact_dir_for_run()`.
    zip_path = os.path.join(artifact_directory, f"{run_id}.zip")
    with open(zip_path, "wb") as f:
        f.write(content)
    return zip_path


def get_artifact_by_name(
    artifacts: List[Dict[str, Any]], name: str, starts_with: bool = False
) -> Optional[Dict[str, Any]]:
    if starts_with:
        return next((a for a in artifacts if a["name"].startswith(name)), None)
    return next((a for a in artifacts if a["name"] == name), None)


def download_artifact_for_run(run_id: str, directory: str) -> None:
    """
    Download the performance artifact for a run_id and extract it to `directory`.
    Uses shared `app.utils.github_utils` functions for GitHub REST and download.
    """
    if os.path.exists(directory):
        return

    artifacts = fetch_artifacts(int(run_id))
    if not artifacts:
        print("Error fetching artifacts for run ID")
        return

    performance_artifact = get_artifact_by_name(artifacts, "playwright_performance_results")
    if not performance_artifact:
        performance_artifact = get_artifact_by_name(
            artifacts, "performance_results_", starts_with=True
        )

    if not performance_artifact:
        print("Error finding performance artifact")
        return

    content = download_artifact_bytes(performance_artifact["archive_download_url"])
    if content is None:
        print("Error downloading artifact content")
        return

    zip_path = _write_zip_for_run(run_id, content)
    baseline_performance_directory = unzip_file(zip_path)
    os.remove(zip_path)
    print(f"Extracted to: {baseline_performance_directory}")


def get_directories_by_type(run_id: str) -> Dict[str, Optional[str]]:
    run_dir = os.path.join(artifact_directory, run_id)

    if not os.path.exists(run_dir):
        return {"playwright": None, "pytest": None, "lighthouse": None}

    # Legacy: if no subfolders exist, treat run_dir as Playwright folder.
    if not any(
        os.path.isdir(os.path.join(run_dir, subfolder)) for subfolder in os.listdir(run_dir)
    ):
        return {"playwright": run_dir, "pytest": None, "lighthouse": None}

    pytest_dir = os.path.join(run_dir, "pytest")
    first_subdir_in_pytest = None
    if os.path.exists(pytest_dir):
        first_subdir_in_pytest = os.path.join(
            pytest_dir,
            next(
                (
                    d
                    for d in os.listdir(pytest_dir)
                    if os.path.isdir(os.path.join(pytest_dir, d))
                ),
                None,
            ),
        )

    return {
        "playwright": os.path.join(run_dir, "playwright"),
        "pytest": first_subdir_in_pytest,
        "lighthouse": os.path.join(run_dir, "lighthouse"),
    }


def remove_artifact_directory() -> None:
    if os.path.exists(artifact_directory):
        print(f"Removing artifact directory: {artifact_directory}")
        shutil.rmtree(artifact_directory)


