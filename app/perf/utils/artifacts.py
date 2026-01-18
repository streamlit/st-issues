from __future__ import annotations

import pathlib
from typing import Any

from app.perf.utils.perf_github_artifacts import (
    extract_run_id_from_url,
    get_artifact_by_name,
    get_build_from_github,
    get_playwright_performance_artifact,
)
from app.perf.utils.test_diff_analyzer import ProcessTestDirectoryOutput, process_test_results_files
from app.utils.github_utils import (
    download_artifact,
    fetch_artifacts,
    iter_json_from_zip_bytes,
    zip_namelist,
)


def _get_performance_artifact_zip_bytes_for_run(run_id: str) -> bytes | None:
    artifacts = fetch_artifacts(int(run_id))
    if not artifacts:
        return None

    performance_artifact = get_artifact_by_name(artifacts, "playwright_performance_results")
    if not performance_artifact:
        performance_artifact = get_artifact_by_name(artifacts, "performance_results_", starts_with=True)
    if not performance_artifact:
        return None

    return download_artifact(performance_artifact["archive_download_url"])


def _extract_playwright_results(zip_bytes: bytes, *, load_all_metrics: bool) -> ProcessTestDirectoryOutput:
    names = zip_namelist(zip_bytes)
    has_playwright_dir = any(n.startswith("playwright/") and n.endswith(".json") and not n.endswith("/") for n in names)
    if has_playwright_dir:
        files_iter = (
            (pathlib.Path(name).name, payload)
            for name, payload in iter_json_from_zip_bytes(zip_bytes, prefix="playwright/")
        )
    else:
        # Legacy: no subfolders -> treat root JSON files as Playwright traces.
        files_iter = (
            (pathlib.Path(name).name, payload) for name, payload in iter_json_from_zip_bytes(zip_bytes, root_only=True)
        )

    return process_test_results_files(files_iter, load_all_metrics=load_all_metrics)


def _extract_lighthouse_scores(zip_bytes: bytes) -> dict[str, float]:
    """Extract Lighthouse performance scores from a performance artifact zip.

    Returns mapping of app key (matching prior `read_json_files` naming) -> score (0..1).
    """
    scores: dict[str, float] = {}
    names = zip_namelist(zip_bytes)
    has_lighthouse_dir = any(n.startswith("lighthouse/") and n.endswith(".json") and not n.endswith("/") for n in names)

    json_iter = (
        iter_json_from_zip_bytes(zip_bytes, prefix="lighthouse/")
        if has_lighthouse_dir
        else iter_json_from_zip_bytes(zip_bytes)
    )

    for member_name, payload in json_iter:
        if not isinstance(payload, dict):
            continue
        try:
            score = payload["categories"]["performance"]["score"]
        except Exception:  # noqa: S112
            continue

        # Keep the same (slightly odd) key derivation behavior as the prior disk-based parser.
        parts = member_name.split("_-_")
        if len(parts) >= 3:
            app_name = parts[1]
            device_type = parts[2]
            key = f"{app_name}_{device_type}"
        else:
            key = member_name

        if isinstance(score, (int, float)):
            scores[key] = float(score)

    return scores


def _extract_pytest_benchmark_json(zip_bytes: bytes) -> dict[str, Any] | None:
    names = zip_namelist(zip_bytes)
    has_pytest_dir = any(n.startswith("pytest/") and n.endswith(".json") and not n.endswith("/") for n in names)

    json_iter = (
        iter_json_from_zip_bytes(zip_bytes, prefix="pytest/") if has_pytest_dir else iter_json_from_zip_bytes(zip_bytes)
    )

    for _, payload in json_iter:
        if isinstance(payload, dict) and "benchmarks" in payload:
            return payload
    return None


def get_artifact_results(
    commit_hash: str, artifact_type: str, *, load_all_metrics: bool = False
) -> tuple[Any, str | None]:
    """Retrieve the artifact results for a given commit hash from GitHub.

    Args:
        commit_hash (str): The commit hash.
        artifact_type (str): The type of artifact to retrieve.
        load_all_metrics (bool): Only relevant for Playwright artifacts; includes tracked metrics.

    Returns:
        tuple: A tuple containing derived results and the build timestamp.
               Returns (None, None) if no artifact is found or the build is not completed.
               Returns ("", "") if the artifact run status is not completed.
    """
    build_data = get_build_from_github(commit_hash)

    if build_data is None:
        return None, None

    artifact_run = get_playwright_performance_artifact(build_data)

    if artifact_run is None:
        return None, None

    if artifact_run.get("status") != "completed":
        return "", ""

    build_timestamp = artifact_run["started_at"]

    run_id = extract_run_id_from_url(artifact_run["details_url"])

    if run_id is None:
        return None, None

    zip_bytes = _get_performance_artifact_zip_bytes_for_run(run_id)
    if not zip_bytes:
        return None, None

    if artifact_type == "playwright":
        return _extract_playwright_results(zip_bytes, load_all_metrics=load_all_metrics), build_timestamp
    if artifact_type == "lighthouse":
        return _extract_lighthouse_scores(zip_bytes), build_timestamp
    if artifact_type == "pytest":
        return _extract_pytest_benchmark_json(zip_bytes), build_timestamp

    return None, None
