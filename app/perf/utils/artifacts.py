from app.perf.utils.perf_github_artifacts import (
    download_artifact_for_run,
    extract_run_id_from_url,
    get_artifact_dir_for_run,
    get_build_from_github,
    get_directories_by_type,
    get_playwright_performance_artifact,
)


def get_artifact_results(hash: str, artifact_type: str):
    """
    Retrieve the artifact results for a given commit hash from GitHub.

    Args:
        hash (str): The commit hash.
        artifact_type (str): The type of artifact to retrieve.

    Returns:
        tuple: A tuple containing the artifact directory and the build timestamp.
               Returns (None, None) if no artifact is found or the build is not completed.
               Returns ("", "") if the artifact run status is not completed.
    """
    build_data = get_build_from_github(hash)

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

    run_directory = get_artifact_dir_for_run(run_id)
    download_artifact_for_run(run_id, run_directory)

    artifact_directory = get_directories_by_type(run_id).get(artifact_type)

    return artifact_directory, build_timestamp
