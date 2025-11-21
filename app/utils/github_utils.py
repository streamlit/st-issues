from __future__ import annotations

from datetime import date
from typing import Any, Dict, Final, List, Literal, Optional

import requests
import streamlit as st

# Streamlit team members:
STREAMLIT_TEAM_MEMBERS = [
    "lukasmasuch",
    "tconkling",
    "vdonato",
    "kmcgrady",
    "mayagbarnes",
    "kajarenrc",
    "willhuang1997",
    "AnOctopus",
    "tvst",
    "kantuni",
    "raethlein",
    "arraydude",
    "snehankekre",
    "akrolsmir",
    "randyzwitch",
    "jrhone",
    "monchier",
    "imjuangarcia",
    "nthmost",
    "blackary",
    "jroes",
    "arnaudmiribel",
    "JessSm3",
    "MathCatsAnd",
    "kasim-inan",
    "astrojams1",
    "gmerticariu",
    "mesmith027",
    "tc87",
    "tyler-simons",
    "lawilby",
    "treuille",
    "Amey-D",
    "CharlyWargnier",
    "kajarenc",
    "karriebear",
    "jrieke",
    "erikhopf",
    "domoritz",
    "dcaminos",
]

# Tests that are expected to be flaky and marked with additional reruns (pytest.mark.flaky(reruns=3))
# This list needs to be updated manually. The test is matched via startswith,
# so it can cover full test scrits or just individual test methods.
EXPECTED_FLAKY_TESTS: Final[list[str]] = [
    "st_video_test.py::test_video_end_time",
    "st_pydeck_chart_select_test.py",
    "st_file_uploader_test.py::test_uploads_directory_with_multiple_files",
    "st_file_uploader_test.py::test_directory_upload_with_file_type_filtering",
    "st_dataframe_interactions_test.py::test_csv_download_button_in_iframe_with_new_tab_host_config",
    "st_dataframe_interactions_test.py::test_csv_download_button_in_iframe",
    "st_video_test.py::test_video_end_time_loop",
    "st_layouts_container_various_elements_test.py::test_layouts_container_expanders",
]


def is_community_author(author: str) -> bool:
    """Check if an author is a community member."""
    return (
        author not in STREAMLIT_TEAM_MEMBERS
        and not author.startswith("sfc-gh-")
        and not author.endswith("[bot]")
    )


def get_headers() -> Dict[str, str]:
    """Get headers for GitHub API requests."""
    return {
        "Authorization": f"token {st.secrets['github']['token']}",
        "Accept": "application/vnd.github.v3+json",
    }


@st.cache_data(ttl=60 * 5)  # cache for 5 minutes
def get_issue_data(repo: str, issue_number: str) -> Optional[Dict[str, Any]]:
    """
    Fetch issue data from GitHub API

    Args:
        repo: Repository in format "owner/repo"
        issue_number: Issue number

    Returns:
        Dictionary containing issue data or None if request fails
    """
    headers = get_headers()
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"

    try:
        response = requests.get(url, headers=headers, timeout=100)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching issue: {str(e)}")
        return None


def extract_issue_metadata(issue_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant metadata from the issue data

    Args:
        issue_data: Raw issue data from GitHub API

    Returns:
        Dictionary with extracted metadata
    """
    return {
        "title": issue_data.get("title", ""),
        "number": issue_data.get("number", ""),
        "state": issue_data.get("state", ""),
        "created_at": issue_data.get("created_at", ""),
        "updated_at": issue_data.get("updated_at", ""),
        "author": issue_data.get("user", {}).get("login", ""),
        "labels": [label.get("name", "") for label in issue_data.get("labels", [])],
        "body": issue_data.get("body", ""),
        "html_url": issue_data.get("html_url", ""),
    }


@st.cache_data(ttl=60 * 5)  # cache for 5 minutes
def get_issue_comments(repo: str, issue_number: str) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch comments for a GitHub issue

    Args:
        repo: Repository in format "owner/repo"
        issue_number: Issue number

    Returns:
        List of comments or None if request fails
    """
    headers = get_headers()
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"

    try:
        response = requests.get(url, headers=headers, timeout=100)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching comments: {str(e)}")
        return None


def extract_comment_data(comment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant data from a comment

    Args:
        comment: Raw comment data from GitHub API

    Returns:
        Dictionary with extracted comment data
    """
    return {
        "id": comment.get("id", ""),
        "body": comment.get("body", ""),
        "created_at": comment.get("created_at", ""),
        "updated_at": comment.get("updated_at", ""),
        "author": comment.get("user", {}).get("login", ""),
        "author_avatar_url": comment.get("user", {}).get("avatar_url", ""),
        "html_url": comment.get("html_url", ""),
    }


def load_issue_data() -> bool:
    """
    Loads issue data based on form input in the session state.
    Returns True if an issue was loaded, False otherwise.

    Assumes the following session state variables:
    - form_issue_number
    - form_repo_info

    Sets the following session state variables:
    - issue_data
    - issue_number
    - repo_info
    - issue_metadata
    - issue_content
    - comments_data
    - processed_comments
    """
    # Process form data after submission
    if (
        not st.session_state.get("form_issue_number")
        or not st.session_state.get("form_issue_number").strip()
    ):
        return False

    # Check if we need to fetch new data
    if (
        st.session_state.get("issue_number") == st.session_state.form_issue_number
        and st.session_state.get("repo_info") == st.session_state.form_repo_info
        and "issue_data" in st.session_state
    ):
        return True

    with st.spinner(
        f"Fetching issue #{st.session_state.form_issue_number} from {st.session_state.form_repo_info}..."
    ):
        # Fetch issue data
        issue_data = get_issue_data(
            st.session_state.form_repo_info,
            st.session_state.form_issue_number,
        )

        if issue_data:
            st.session_state.issue_data = issue_data
            st.session_state.issue_number = st.session_state.form_issue_number
            st.session_state.repo_info = st.session_state.form_repo_info
            st.success(
                f"Successfully fetched issue #{st.session_state.form_issue_number}"
            )

            # Extract and store issue metadata
            issue_metadata = extract_issue_metadata(issue_data)
            st.session_state.issue_metadata = issue_metadata
            st.session_state.issue_content = issue_data.get("body", "")

            # Fetch issue comments
            with st.spinner("Fetching issue comments..."):
                comments_data = get_issue_comments(
                    st.session_state.form_repo_info,
                    st.session_state.form_issue_number,
                )

            if comments_data:
                st.session_state.comments_data = comments_data
                # Extract relevant comment data
                processed_comments = [
                    extract_comment_data(comment) for comment in comments_data
                ]
                st.session_state.processed_comments = processed_comments
            else:
                st.session_state.comments_data = []
                st.session_state.processed_comments = []

            return True
        else:
            st.error(
                f"Failed to fetch issue #{st.session_state.form_issue_number}. Please check the repository and issue number."
            )
            return False


@st.cache_data(ttl=60 * 60 * 12)  # cache for 12 hours
def get_all_github_issues(
    state: Literal["open", "closed", "all"] = "all",
) -> List[Dict[str, Any]]:
    """Paginate through all issues in the streamlit/streamlit repo
    and return them all as a list of dicts."""
    issues = []
    state_param = f"state={state}" if state else ""
    url: str | None = (
        f"https://api.github.com/repos/streamlit/streamlit/issues?{state_param}&per_page=100"
    )

    while url:
        try:
            response = requests.get(
                url,
                headers=get_headers(),
                timeout=100,
            )

            if response.status_code == 200:
                data = response.json()
                if not data:
                    break
                issues.extend(data)

                # Parse Link header to get next page URL
                link_header = response.headers.get("Link", "")
                url = None
                if link_header:
                    links = link_header.split(",")
                    for link in links:
                        if 'rel="next"' in link:
                            url = link.split(";")[0].strip().strip("<>")
                            break
            else:
                st.error(
                    f"Failed to retrieve data: {response.status_code}: {response.text}"
                )
                break
        except Exception as ex:
            st.error(f"Failed to retrieve issues: {ex}")
            break
    return issues


@st.cache_data(ttl=60 * 60 * 24)  # cache for 24 hours
def get_all_github_prs(
    state: Literal["open", "closed", "all"] = "all",
) -> List[Dict[str, Any]]:
    """Paginate through all PRs in the streamlit/streamlit repo
    and return them all as a list of dicts."""
    prs = []
    state_param = f"state={state}" if state else ""
    url: str | None = (
        f"https://api.github.com/repos/streamlit/streamlit/pulls?{state_param}&per_page=100"
    )

    while url:
        try:
            response = requests.get(
                url,
                headers=get_headers(),
                timeout=100,
            )

            if response.status_code == 200:
                data = response.json()
                if not data:
                    break
                prs.extend(data)

                # Parse Link header to get next page URL
                link_header = response.headers.get("Link", "")
                url = None
                if link_header:
                    links = link_header.split(",")
                    for link in links:
                        if 'rel="next"' in link:
                            url = link.split(";")[0].strip().strip("<>")
                            break
            else:
                st.error(
                    f"Failed to retrieve data: {response.status_code}: {response.text}"
                )
                break
        except Exception as ex:
            st.error(f"Failed to retrieve PRs: {ex}")
            break
    return prs


@st.cache_data(
    ttl=60 * 60 * 24, show_spinner="Fetching workflow runs..."
)  # cache for 24 hours
def fetch_workflow_runs(
    workflow_name: str,
    limit: int = 50,
    since: date | None = None,
    branch: str | None = "develop",
    status: str | None = "success",
) -> List[Dict[str, Any]]:
    """Fetch workflow runs for a specific workflow."""
    all_runs: List[Dict[str, Any]] = []
    page = 1
    per_page = 100

    params: Dict[str, Any] = {
        "per_page": per_page,
        "page": page,
    }
    if branch:
        params["branch"] = branch
    if status:
        params["status"] = status
    if since:
        params["created"] = f">{since.isoformat()}"

    while len(all_runs) < limit:
        params["page"] = page
        params["per_page"] = min(per_page, limit - len(all_runs))
        try:
            response = requests.get(
                f"https://api.github.com/repos/streamlit/streamlit/actions/workflows/{workflow_name}/runs",
                headers=get_headers(),
                params=params,
                timeout=30,
            )

            if response.status_code != 200:
                st.error(f"Error fetching workflow runs: {response.status_code}")
                break

            data = response.json()
            runs = data.get("workflow_runs", [])

            if not runs:
                break

            all_runs.extend(runs)

            if len(runs) < per_page:
                break

            page += 1

        except Exception as e:
            st.error(f"Error fetching workflow runs: {e}")
            break

    return all_runs[:limit]


@st.cache_data(show_spinner="Fetching artifacts...")
def fetch_artifacts(run_id: int) -> List[Dict[str, Any]]:
    """Fetch artifacts for a specific workflow run."""
    try:
        response = requests.get(
            f"https://api.github.com/repos/streamlit/streamlit/actions/runs/{run_id}/artifacts",
            headers=get_headers(),
            timeout=30,
        )

        if response.status_code != 200:
            st.error(f"Error fetching artifacts: {response.status_code}")
            return []

        return response.json().get("artifacts", [])
    except Exception as e:
        st.error(f"Error fetching artifacts: {e}")
        return []


@st.cache_data(show_spinner=False)
def download_artifact(artifact_url: str) -> Optional[bytes]:
    """Download an artifact from GitHub Actions."""
    try:
        # The artifact URL is a redirect, so we need to get the real URL.
        redirect_response = requests.get(
            artifact_url, headers=get_headers(), timeout=60, allow_redirects=False
        )
        if redirect_response.status_code != 302:
            st.error(
                f"Error getting artifact redirect URL: {redirect_response.status_code}"
            )
            return None

        download_url = redirect_response.headers["Location"]

        # Download the artifact content from the redirect URL without auth headers
        response = requests.get(download_url, timeout=60)

        if response.status_code != 200:
            st.error(f"Error downloading artifact: {response.status_code}")
            return None

        return response.content
    except Exception as e:
        st.error(f"Error downloading artifact: {e}")
        return None


def fetch_pr_info(pr_number: str) -> Optional[Dict[str, Any]]:
    """Fetch information about a PR from GitHub API."""
    try:
        response = requests.get(
            f"https://api.github.com/repos/streamlit/streamlit/pulls/{pr_number}",
            headers=get_headers(),
            timeout=30,
        )

        if response.status_code != 200:
            st.error(f"Error fetching PR info: {response.status_code}")
            return None

        return response.json()
    except Exception as e:
        st.error(f"Error fetching PR info: {e}")
        return None


@st.cache_data(ttl=60 * 60 * 3, show_spinner=False)
def fetch_pr_reviews(pr_number: int) -> List[Dict[str, Any]]:
    """Fetch all reviews for a given PR."""
    reviews: List[Dict[str, Any]] = []
    page = 1

    while True:
        try:
            response = requests.get(
                f"https://api.github.com/repos/streamlit/streamlit/pulls/{pr_number}/reviews",
                headers=get_headers(),
                params={"per_page": 100, "page": page},
                timeout=30,
            )

            if response.status_code != 200:
                st.error(
                    f"Error fetching PR reviews for #{pr_number}: {response.status_code}"
                )
                break

            data = response.json()
            if not data:
                break

            reviews.extend(data)

            if len(data) < 100:
                break

            page += 1
        except Exception as e:
            st.error(f"Error fetching PR reviews for #{pr_number}: {e}")
            break

    return reviews


def fetch_workflow_runs_for_commit(
    commit_sha: str, workflow_name: str
) -> List[Dict[str, Any]]:
    """Fetch workflow runs for a specific commit."""
    try:
        response = requests.get(
            f"https://api.github.com/repos/streamlit/streamlit/actions/workflows/{workflow_name}/runs?head_sha={commit_sha}&status=success",
            headers=get_headers(),
            timeout=30,
        )

        if response.status_code != 200:
            st.error(f"Error fetching workflow runs for commit: {response.status_code}")
            return []

        return response.json().get("workflow_runs", [])
    except Exception as e:
        st.error(f"Error fetching workflow runs for commit: {e}")
        return []


@st.cache_data(show_spinner=False)
def fetch_workflow_run_annotations(check_run_id: str) -> list[dict]:
    annotations_url = f"https://api.github.com/repos/streamlit/streamlit/check-runs/{check_run_id}/annotations"
    response = requests.get(annotations_url, headers=get_headers())

    if response.status_code == 200:
        return response.json()
    st.error(f"Error fetching annotations: {response.status_code}")
    return []


@st.cache_data(show_spinner=False)
def fetch_workflow_runs_ids(check_suite_id: str) -> list[str]:
    annotations_url = f"https://api.github.com/repos/streamlit/streamlit/check-suites/{check_suite_id}/check-runs"
    response = requests.get(annotations_url, headers=get_headers())

    if response.status_code == 200:
        check_runs = response.json()["check_runs"]
        check_runs = [
            check_run
            for check_run in check_runs
            if check_run["conclusion"] == "success"
        ]
        return [check_run["id"] for check_run in check_runs]
    st.error(f"Error fetching annotations: {response.status_code}")
    return []


def extract_issue_number(github_url: str) -> int:
    """Extract issue number from GitHub URL."""
    if "/issues/" in github_url:
        try:
            return int(github_url.split("/issues/")[-1].split("?")[0].split("#")[0])
        except (ValueError, IndexError):
            return 0
    return 0


def validate_issue_number(issue_str):
    """Validate issue number is between 1 and 150,000."""
    try:
        issue_num = int(issue_str.strip())
        if 1 <= issue_num <= 150000:
            return True, issue_num
        else:
            return False, None
    except (ValueError, TypeError):
        return False, None


def parse_github_url(url):
    """Parse GitHub issue URL to extract repository and issue number."""
    import re

    if not url or not url.strip():
        return None, None

    url = url.strip()

    # Remove @ symbol if present at the beginning
    if url.startswith("@"):
        url = url[1:]

    # Pattern to match GitHub issue URLs
    pattern = r"https://github\.com/([^/]+/[^/]+)/issues/(\d+)"
    match = re.match(pattern, url)

    if match:
        repo_info = match.group(1)
        issue_number = match.group(2)
        return repo_info, issue_number

    return None, None
