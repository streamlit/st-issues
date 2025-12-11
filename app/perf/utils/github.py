import json
import os
import re
import shutil
import zipfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests


def get_headers(token: str):
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


this_file_directory = os.path.dirname(os.path.realpath(__file__))
artifact_directory = os.path.abspath(
    os.path.join(this_file_directory, "../../artifacts")
)


def make_http_request(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Union[str, int]]] = None,
) -> requests.Response:
    """
    Make an HTTP GET request.

    Args:
        url (str): The URL to make the request to.
        headers (Optional[Dict[str, str]]): Optional dictionary of headers.
        params (Optional[Dict[str, Union[str, int]]]): Optional dictionary of query parameters.

    Returns:
        requests.Response: The HTTP response object.
    """
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response


def make_github_request(
    url: str, params: Optional[Dict[str, Union[str, int]]], token: str
) -> Dict[str, Any]:
    """
    Make a GET request to the GitHub API.

    Args:
        url (str): The URL to make the request to.
        params (Optional[Dict[str, Union[str, int]]]): Optional dictionary of query parameters.

    Returns:
        Dict: The JSON response from the GitHub API.
    """
    response = make_http_request(url, headers=get_headers(token=token), params=params)
    return response.json()  # type: ignore


def append_to_performance_scores(
    performance_scores: Dict[str, Dict[str, float]],
    datetime: str,
    app_name: str,
    score: float,
) -> None:
    """
    Append a performance score to the performance_scores dictionary.

    Args:
        performance_scores (Dict[str, Dict[str, float]]): Dictionary to store performance scores.
        datetime (str): The datetime key for the performance score.
        app_name (str): The name of the application.
        score (float): The performance score to append.

    Returns:
        None
    """
    if datetime not in performance_scores:
        performance_scores[datetime] = {}
    performance_scores[datetime][app_name] = score


def download_artifact(download_url: str, artifact_name: str, token: str) -> str:
    """
    Download an artifact from a given URL and save it as a zip file in the
    ./artifacts directory.

    Args:
        download_url (str): The URL to download the artifact from.
        artifact_name (str): The name to save the downloaded artifact as.

    Returns:
        str: The path to the downloaded zip file.
    """
    response = requests.get(download_url, headers=get_headers(token=token))
    os.makedirs(artifact_directory, exist_ok=True)
    zip_path = os.path.join(artifact_directory, f"{artifact_name}.zip")
    with open(zip_path, "wb") as f:
        f.write(response.content)
    return zip_path


def unzip_file(zip_path: str) -> str:
    """
    Unzip a zip file to a directory in the ./artifacts directory that has the same name as the file.

    Args:
        zip_path (str): The path to the zip file.

    Returns:
        str: The path to the directory where the zip file was extracted.
    """
    file_name = os.path.splitext(os.path.basename(zip_path))[0]
    extract_to = os.path.join(artifact_directory, file_name)
    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)
    return extract_to


def read_json_files(
    performance_scores: Dict[str, Dict[str, float]],
    timestamp: str,
    directory: str,
) -> None:
    """
    Read JSON files from a directory and append their performance scores to the
    performance_scores dictionary.

    Args:
        performance_scores (Dict[str, Dict[str, float]]): Dictionary to store performance scores.
        artifact (Dict[str, Any]): Dictionary containing artifact metadata.
        directory (str): The directory to search for JSON files.

    Returns:
        None
    """
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                json_path = os.path.join(root, file)
                with open(json_path, "r") as json_file:
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
    token: str,
) -> Dict[str, Dict[str, float]]:
    """
    Process an artifact by downloading, unzipping, and reading its JSON files.

    Args:
        performance_scores (Dict[str, Dict[str, float]]): Dictionary to store performance scores.
        artifact (Dict[str, Any]): Dictionary containing artifact metadata.

    Returns:
        Dict[str, Dict[str, float]]: Updated performance_scores dictionary.
    """
    download_url = artifact["archive_download_url"]
    artifact_name = artifact["name"]
    zip_path = download_artifact(download_url, artifact_name, token)
    extracted_dir = unzip_file(zip_path)
    read_json_files(performance_scores, artifact, extracted_dir)
    return performance_scores


def get_all_prs_with_label(label: str, token: str) -> List[Dict[str, Any]]:
    """
    Get all pull requests with a specific label.

    Args:
        label (str): The label to filter pull requests by.

    Returns:
        List[Dict[str, Any]]: A list of pull requests with the specified label.
    """
    prs_url = "https://api.github.com/repos/streamlit/streamlit/pulls"
    prs_response = requests.get(prs_url, headers=get_headers(token=token))
    prs = prs_response.json()

    prs_with_label = [
        pr for pr in prs if any(lbl["name"] == label for lbl in pr["labels"])
    ]
    return prs_with_label


def get_workflow_run_id(ref: str, workflow_name: str, token: str) -> Optional[int]:
    """
    Get the workflow run ID for a specific branch and workflow name.

    Args:
        ref (str): The branch reference (e.g., 'refs/heads/main').
        workflow_name (str): The name of the workflow to find.
        token (str): The GitHub token for authentication.

    Returns:
        Optional[int]: The ID of the workflow run if found, otherwise None.
    """
    url = "https://api.github.com/repos/streamlit/streamlit/actions/runs"
    params = {"event": "pull_request", "branch": ref}
    response = requests.get(url, headers=get_headers(token=token), params=params)
    response.raise_for_status()
    workflow_runs = response.json()["workflow_runs"]

    for run in workflow_runs:
        if run["name"] == workflow_name:
            return run["id"]

    return None


def get_nightly_builds(token: str, per_page: int = 5) -> Dict[str, Any]:
    """
    Get the nightly builds from GitHub.

    Args:
        token (str): The GitHub token for authentication.
        per_page (int): The number of builds to return per page.

    Returns:
        Dict[str, Any]: The nightly builds data from GitHub.
    """
    url = "https://api.github.com/repos/streamlit/streamlit/actions/workflows/nightly.yml/runs"
    params = {"per_page": per_page}
    response = requests.get(url, headers=get_headers(token=token), params=params)
    response.raise_for_status()
    return response.json()


def get_commit_hashes_for_branch_name(
    branch_name: str, token: str, limit: int = 50, until_date: Optional[str] = None
) -> List[str]:
    """
    Get the commit hashes for a specific branch name.

    Args:
        branch_name (str): The name of the branch to find commit hashes for.
        token (str): The GitHub token for authentication.
        limit (int): The number of commits to return.
        until_date (Optional[str]): ISO format date string to get commits until (inclusive).

    Returns:
        List[str]: A list of commit hashes for the specified branch.
    """
    url = "https://api.github.com/repos/streamlit/streamlit/commits"
    params = {"sha": branch_name, "per_page": limit}
    if until_date:
        params["until"] = f"{until_date}T23:59:59Z"

    response = requests.get(url, headers=get_headers(token=token), params=params)
    response.raise_for_status()
    commits = response.json()
    return [commit["sha"] for commit in commits]


def get_check_run_by_name(
    workflow_runs: List[Dict[str, Any]], name: str
) -> Optional[Dict[str, Any]]:
    """
    Get a check run by name from a list of check runs.

    Args:
        workflow_runs (List[Dict[str, Any]]): The list of check runs.
        name (str): The name of the check run to find.

    Returns:
        Optional[Dict[str, Any]]: The check run with the specified name, or None if not found.
    """
    return next(
        (run for run in workflow_runs if run["name"] == name),
        None,
    )


def get_shortest_check_run_by_name(
    workflow_runs: List[Dict[str, Any]], name: str
) -> Optional[Dict[str, Any]]:
    """
    Get the shortest check run by name from a list of check runs.

    Args:
        workflow_runs (List[Dict[str, Any]]): The list of check runs.
        name (str): The name of the check run to find.

    Returns:
        Optional[Dict[str, Any]]: The shortest check run with the specified name, or None if not found.
    """
    shortest_check_run = None
    shortest_duration = float("inf")

    for check_run in workflow_runs:
        if check_run["name"] == name and check_run["status"] == "completed":
            started_at = datetime.strptime(
                check_run["started_at"], "%Y-%m-%dT%H:%M:%SZ"
            )
            completed_at = datetime.strptime(
                check_run["completed_at"], "%Y-%m-%dT%H:%M:%SZ"
            )
            duration = (completed_at - started_at).total_seconds()
            if duration < shortest_duration:
                shortest_duration = duration
                shortest_check_run = check_run

    return shortest_check_run


def get_build_from_github(commit_hash: str, token: str) -> Optional[Dict[str, Any]]:
    """
    Get all workflow runs from GitHub for a specific commit hash.

    Args:
        commit_hash (str): The commit hash to get the workflow runs for.
        token (str): The GitHub token for authentication.

    Returns:
        Optional[Dict[str, Any]]: Dictionary containing workflow runs data or None if error.
    """
    try:
        # Use the workflow runs API filtered by the commit SHA
        url = "https://api.github.com/repos/streamlit/streamlit/actions/runs"
        params = {"head_sha": commit_hash}
        response = make_github_request(url, params, token)

        # Transform the response to match the expected format
        workflow_runs = response.get("workflow_runs", [])
        return {
            "status": "completed" if workflow_runs else "not_found",
            "workflow_runs": [
                {
                    "name": run["name"],
                    "status": run["status"],
                    "started_at": run["run_started_at"],
                    "completed_at": run["updated_at"],
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
    """
    Get the playwright performance artifact from the build data.

    Args:
        build_data (Dict[str, Any]): The build data from GitHub.

    Returns:
        Optional[Dict[str, Any]]: The playwright performance artifact, or None if not found.
    """
    performance_run = get_check_run_by_name(
        build_data["workflow_runs"], "Performance Suite"
    )

    # NOTE: As of 1/17/2025 we have a single Performance suite in CI. Before
    # this, we had a few other scattered job names. I am leaving these here so
    # that we can still get the data we expect from the older runs.
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


def extract_run_id_from_url(url: str) -> Optional[str]:
    """
    Extract the run ID from a GitHub actions URL.

    Args:
        url (str): The URL to extract the run ID from.

    Returns:
        Optional[str]: The extracted run ID, or None if not found.
    """
    match = re.search(r"/runs/(\d+)", url)
    result = match.group(1) if match else None
    return result


def get_artifact_dir_for_run(run_id: str) -> str:
    """
    Get the artifact directory for a specific run ID.

    Args:
        run_id (str): The run ID to get the artifact directory for.

    Returns:
        str: The path to the artifact directory.
    """
    return os.path.join(artifact_directory, run_id)


def get_artifact_for_run_id(run_id: str, token: str) -> Optional[Dict[str, Any]]:
    """
    Get the artifacts for a specific run ID from GitHub.

    Args:
        run_id (str): The run ID to get the artifacts for.
        token (str): The GitHub token for authentication.

    Returns:
        Optional[Dict[str, Any]]: The artifact data from GitHub.
    """
    try:
        url = f"https://api.github.com/repos/streamlit/streamlit/actions/runs/{run_id}/artifacts"
        response = make_github_request(url, None, token)
        return response
    except Exception as error:
        print(f"Error fetching artifact from GitHub: {error}")
        return None


def get_artifact_by_name(
    artifacts: List[Dict[str, Any]], name: str, starts_with: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Get an artifact by name from a list of artifacts.

    Args:
        artifacts (List[Dict[str, Any]]): The list of artifacts.
        name (str): The name of the artifact to find.
        starts_with (bool): Whether to match artifacts that start with the name.

    Returns:
        Optional[Dict[str, Any]]: The artifact with the specified name, or None if not found.
    """
    if starts_with:
        return next(
            (artifact for artifact in artifacts if artifact["name"].startswith(name)),
            None,
        )
    return next((artifact for artifact in artifacts if artifact["name"] == name), None)


def download_artifact_for_run(run_id: str, directory: str, token: str) -> None:
    """
    Download the artifact for a specific run ID and extract it to a directory.

    Args:
        run_id (str): The run ID to download the artifact for.
        directory (str): The directory to extract the artifact to.
        token (str): The GitHub token for authentication.

    Returns:
        None
    """
    if not os.path.exists(directory):
        artifact_data = get_artifact_for_run_id(run_id, token)

        if not artifact_data:
            print("Error fetching artifact for run ID")
            return

        performance_artifact = get_artifact_by_name(
            artifact_data["artifacts"], "playwright_performance_results"
        )

        if not performance_artifact:
            performance_artifact = get_artifact_by_name(
                artifact_data["artifacts"], "performance_results_", starts_with=True
            )

        if not performance_artifact:
            print("Error finding performance artifact")
            return

        downloaded_zip_path = download_artifact(
            performance_artifact["archive_download_url"], run_id, token
        )

        baseline_performance_directory = unzip_file(downloaded_zip_path)
        os.remove(downloaded_zip_path)

        print(f"Extracted to: {baseline_performance_directory}")


def get_directories_by_type(run_id: str) -> Dict[str, Optional[str]]:
    """
    Get the directories by type for a specific run ID.

    Args:
        run_id (str): The run ID to get the directories for.

    Returns:
        Dict[str, Optional[str]]: A dictionary with keys 'playwright', 'pytest',
        and 'lighthouse', and their corresponding directory paths as values.
    """
    run_dir = os.path.join(artifact_directory, run_id)

    if not os.path.exists(run_dir):
        return {
            "playwright": None,
            "pytest": None,
            "lighthouse": None,
        }

    # For legacy purposes, if there are no subfolders in the run_dir, just
    # return the run_dir for Playwright
    if not any(
        os.path.isdir(os.path.join(run_dir, subfolder))
        for subfolder in os.listdir(run_dir)
    ):
        return {
            "playwright": run_dir,
            "pytest": None,
            "lighthouse": None,
        }

    # Pytest-benchmark puts all its results in a subfolder named after the type
    # of hardware it's running on. So we'll just take the first subdirectory we
    # find in the pytest folder
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
    """
    Remove the entire artifact directory.

    Returns:
        None
    """
    if os.path.exists(artifact_directory):
        print(f"Removing artifact directory: {artifact_directory}")
        shutil.rmtree(artifact_directory)
