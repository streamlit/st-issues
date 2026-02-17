from __future__ import annotations

import base64
import contextlib
import json
import urllib.parse
from io import BytesIO
from typing import TYPE_CHECKING, Any, Final, Literal, cast
from zipfile import ZipFile

import requests
import streamlit as st

if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import date

# Streamlit team members:

ACTIVTE_STREAMLIT_TEAM_MEMBERS = [
    "lukasmasuch",
    "kmcgrady",
    "mayagbarnes",
    "jrieke",
    "sfc-gh-lwilby",
    "sfc-gh-bnisco",
    "sfc-gh-nbellante",
    "sfc-gh-tteixeira",
    "sfc-gh-dmatthews",
    "sfc-gh-lmasuch",
]

STREAMLIT_TEAM_MEMBERS = [
    *ACTIVTE_STREAMLIT_TEAM_MEMBERS,
    "tconkling",
    "kajarenc",
    "willhuang1997",
    "AnOctopus",
    "vdonato",
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
    "karriebear",
    "erikhopf",
    "domoritz",
    "dcaminos",
    "aaj-st",
    "sfc-gh-jcarroll",
    "sfc-gh-aamadhavan",
    "sfc-gh-smohile",
    "sfc-gh-mnowotka",
    "sfc-gh-tszerszen",
    "sfc-gh-dswiecki",
    "sfc-gh-wihuang",
    "sfc-gh-kjavadyan",
    "sfc-gh-kbregula",
    "sfc-gh-pchiu",
    "sfc-gh-jgarcia",
    "sfc-gh-jkinkead",
    "sfc-gh-kmcgrady",
    "sfc-gh-jrieke",
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
    "forward_msg_cache_test.py::test_check_total_websocket_message_number_and_size",
]


def is_community_author(author: str) -> bool:
    """Check if an author is a community member."""
    return author not in STREAMLIT_TEAM_MEMBERS and not author.startswith("sfc-gh-") and not author.endswith("[bot]")


def get_headers() -> dict[str, str]:
    """Get headers for GitHub API requests."""
    return {
        "Authorization": f"token {st.secrets['github']['token']}",
        "Accept": "application/vnd.github.v3+json",
    }


def _compact_error_text(text: str, max_chars: int = 280) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return f"{compact[:max_chars].rstrip()}..."


def _request_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: int = 30,
    expected_statuses: set[int] | None = None,
) -> tuple[Any | None, str | None, int | None]:
    """Perform a GitHub GET request and decode JSON without UI side effects."""
    expected = expected_statuses or {200}
    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=timeout)
    except requests.RequestException as exc:
        return None, f"Request failed for {url}: {exc!s}", None

    if response.status_code not in expected:
        error = f"Request to {url} failed with status {response.status_code}: {_compact_error_text(response.text)}"
        return None, error, response.status_code

    if response.status_code == 204:
        return None, None, response.status_code

    try:
        return response.json(), None, response.status_code
    except ValueError as exc:
        return None, f"Failed to decode JSON from {url}: {exc!s}", response.status_code


class _PartialDataError(Exception):
    def __init__(self, message: str, partial_data: Any) -> None:
        super().__init__(message)
        self.partial_data = partial_data


@st.cache_data(ttl=60 * 10, max_entries=256, show_spinner=False)
def fetch_issue_payload(repo: str, issue_number: int | str) -> tuple[dict[str, Any] | None, str | None]:
    """Fetch issue payload and return (data, error_message)."""
    payload, error, status = _request_json(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}",
        timeout=100,
        expected_statuses={200, 404},
    )
    if status == 404:
        return None, None
    if error:
        return None, error
    return cast("dict[str, Any]", payload), None


@st.cache_data(ttl=60 * 10, max_entries=256, show_spinner=False)
def _fetch_issue_comments_payload_cached(repo: str, issue_number: int | str) -> list[dict[str, Any]]:
    """Fetch all issue comments, raising if a later page fails."""
    comments: list[dict[str, Any]] = []
    page = 1

    while True:
        payload, error, status = _request_json(
            f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments",
            params={"per_page": 100, "page": page},
            timeout=100,
            expected_statuses={200, 404},
        )
        if status == 404:
            return comments
        if error:
            raise _PartialDataError(error, comments)

        page_items = cast("list[dict[str, Any]]", payload)
        if not page_items:
            break
        comments.extend(page_items)
        if len(page_items) < 100:
            break
        page += 1

    return comments


def _fetch_issue_comments_payload(repo: str, issue_number: int | str) -> tuple[list[dict[str, Any]], str | None]:
    """Fetch all issue comments and return (comments, error_message)."""
    try:
        return _fetch_issue_comments_payload_cached(repo, issue_number), None
    except _PartialDataError as exc:
        return cast("list[dict[str, Any]]", exc.partial_data), str(exc)


class _IssueCommentsPayloadFetcher:
    def __call__(self, repo: str, issue_number: int | str) -> tuple[list[dict[str, Any]], str | None]:
        return _fetch_issue_comments_payload(repo, issue_number)

    def clear(self) -> None:
        _fetch_issue_comments_payload_cached.clear()


fetch_issue_comments_payload = _IssueCommentsPayloadFetcher()


@st.cache_data(ttl=60 * 60, max_entries=1024, show_spinner=False)
def _fetch_issue_reactions_cached(repo: str, issue_number: int) -> list[dict[str, Any]]:
    """Fetch all issue reactions, raising if a later page fails."""
    reactions: list[dict[str, Any]] = []
    page = 1

    while True:
        payload, error, status = _request_json(
            f"https://api.github.com/repos/{repo}/issues/{issue_number}/reactions",
            params={"per_page": 100, "page": page},
            timeout=30,
            expected_statuses={200, 404},
        )
        if status == 404:
            return reactions
        if error:
            raise _PartialDataError(error, reactions)

        page_items = cast("list[dict[str, Any]]", payload)
        if not page_items:
            break
        reactions.extend(page_items)
        if len(page_items) < 100:
            break
        page += 1

    return reactions


def _fetch_issue_reactions(repo: str, issue_number: int) -> tuple[list[dict[str, Any]], str | None]:
    """Fetch all issue reactions and return (reactions, error_message)."""
    try:
        return _fetch_issue_reactions_cached(repo, issue_number), None
    except _PartialDataError as exc:
        return cast("list[dict[str, Any]]", exc.partial_data), str(exc)


class _IssueReactionsFetcher:
    def __call__(self, repo: str, issue_number: int) -> tuple[list[dict[str, Any]], str | None]:
        return _fetch_issue_reactions(repo, issue_number)

    def clear(self) -> None:
        _fetch_issue_reactions_cached.clear()


fetch_issue_reactions = _IssueReactionsFetcher()


@st.cache_data(ttl=60 * 60, max_entries=2048, show_spinner=False)
def fetch_github_user_profile(username: str) -> tuple[dict[str, Any] | None, str | None]:
    """Fetch a GitHub user profile by login."""
    if not username:
        return None, None

    payload, error, status = _request_json(
        f"https://api.github.com/users/{username}",
        timeout=30,
        expected_statuses={200, 404},
    )
    if status == 404:
        return None, None
    if error:
        return None, error
    return cast("dict[str, Any]", payload), None


@st.cache_data(ttl=60 * 60, max_entries=256, show_spinner=False)
def fetch_github_user_profiles(usernames: tuple[str, ...]) -> tuple[dict[str, dict[str, Any] | None], list[str]]:
    """Fetch user profiles for a set of usernames with one request per unique login."""
    profiles: dict[str, dict[str, Any] | None] = {}
    errors: list[str] = []
    for username in sorted({name for name in usernames if name}):
        profile, error = fetch_github_user_profile(username)
        profiles[username] = profile
        if error:
            errors.append(error)
    return profiles, errors


@st.cache_data(ttl=300, max_entries=256, show_spinner=False)
def fetch_pull_request_payload(repo: str, pr_number: int) -> tuple[dict[str, Any] | None, str | None]:
    """Fetch pull request details and return (data, error_message)."""
    payload, error, status = _request_json(
        f"https://api.github.com/repos/{repo}/pulls/{pr_number}",
        timeout=100,
        expected_statuses={200, 404},
    )
    if status == 404:
        return None, None
    if error:
        return None, error
    return cast("dict[str, Any]", payload), None


@st.cache_data(ttl=300, max_entries=256, show_spinner=False)
def _fetch_pull_request_files_payload_cached(repo: str, pr_number: int) -> list[dict[str, Any]]:
    """Fetch all changed files for a pull request, raising on later-page failures."""
    files: list[dict[str, Any]] = []
    page = 1

    while True:
        payload, error, status = _request_json(
            f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files",
            params={"per_page": 100, "page": page},
            timeout=100,
            expected_statuses={200, 404},
        )
        if status == 404:
            return files
        if error:
            raise _PartialDataError(error, files)

        page_items = cast("list[dict[str, Any]]", payload)
        if not page_items:
            break
        files.extend(page_items)
        if len(page_items) < 100:
            break
        page += 1

    return files


def fetch_pull_request_files_payload(repo: str, pr_number: int) -> tuple[list[dict[str, Any]], str | None]:
    """Fetch all changed files for a pull request."""
    try:
        return _fetch_pull_request_files_payload_cached(repo, pr_number), None
    except _PartialDataError as exc:
        return cast("list[dict[str, Any]]", exc.partial_data), str(exc)


fetch_pull_request_files_payload.clear = _fetch_pull_request_files_payload_cached.clear  # type: ignore[attr-defined]


@st.cache_data(ttl=300, max_entries=256, show_spinner=False)
def fetch_repo_file_text_at_ref(repo: str, path: str, ref: str) -> tuple[str | None, str | None]:
    """Fetch text content for a repository file at a specific ref."""
    payload, error, status = _request_json(
        f"https://api.github.com/repos/{repo}/contents/{path}",
        params={"ref": ref},
        timeout=100,
        expected_statuses={200, 404},
    )
    if status == 404:
        return None, None
    if error:
        return None, error

    content_b64 = cast("dict[str, Any]", payload).get("content")
    if not isinstance(content_b64, str):
        return None, f"No content returned for {path} at {ref}"

    try:
        return base64.b64decode(content_b64).decode("utf-8"), None
    except Exception as exc:
        return None, f"Failed decoding content for {path}: {exc!s}"


@st.cache_data(ttl=60 * 60 * 12, max_entries=128, show_spinner=False)
def _fetch_issue_view_counts_cached(issue_numbers: tuple[int, ...]) -> dict[int, int | None]:
    """Fetch view counts from views-badge.org in batches, raising on any batch failure."""
    unique_issues = sorted(set(issue_numbers))
    if not unique_issues:
        return {}

    view_counts: dict[int, int | None] = {}
    batch_size = 100

    errors: list[str] = []

    for i in range(0, len(unique_issues), batch_size):
        batch = unique_issues[i : i + batch_size]
        keys = ",".join(f"st-issue-{num}" for num in batch)
        url = f"https://api.views-badge.org/stats-batch?keys={keys}"
        try:
            response = requests.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    )
                },
                timeout=30,
            )
        except requests.RequestException as exc:
            errors.append(f"Failed to fetch issue views for batch starting at issue #{batch[0]}: {exc!s}")
            continue

        if response.status_code != 200:
            errors.append(
                f"Failed to fetch issue views ({response.status_code}) for batch starting at issue #{batch[0]}: "
                f"{_compact_error_text(response.text)}"
            )
            continue

        try:
            data = response.json()
        except ValueError as exc:
            errors.append(f"Failed to decode issue views response for batch starting at issue #{batch[0]}: {exc!s}")
            continue
        if not isinstance(data, dict):
            errors.append(
                f"Unexpected issue views payload type for batch starting at issue #{batch[0]}: {type(data).__name__}"
            )
            continue

        for key, value in data.items():
            with contextlib.suppress(ValueError):
                issue_num = int(str(key).split("-")[-1])
                views = value.get("views") if isinstance(value, dict) else None
                view_counts[issue_num] = int(views) if isinstance(views, int) else None

    if errors:
        raise _PartialDataError(" ; ".join(errors), view_counts)

    return view_counts


def _fetch_issue_view_counts(issue_numbers: tuple[int, ...]) -> tuple[dict[int, int | None], str | None]:
    """Fetch view counts from views-badge.org in batches."""
    try:
        return _fetch_issue_view_counts_cached(issue_numbers), None
    except _PartialDataError as exc:
        return cast("dict[int, int | None]", exc.partial_data), str(exc)


class _IssueViewCountsFetcher:
    def __call__(self, issue_numbers: tuple[int, ...]) -> tuple[dict[int, int | None], str | None]:
        return _fetch_issue_view_counts(issue_numbers)

    def clear(self) -> None:
        _fetch_issue_view_counts_cached.clear()


fetch_issue_view_counts = _IssueViewCountsFetcher()


@st.cache_data(ttl=60 * 5)  # cache for 5 minutes
def get_issue_data(repo: str, issue_number: str) -> dict[str, Any] | None:
    """Fetch issue data from GitHub API.

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
        st.error(f"Error fetching issue: {e!s}")
        return None


def extract_issue_metadata(issue_data: dict[str, Any]) -> dict[str, Any]:
    """Extract relevant metadata from the issue data.

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
def get_issue_comments(repo: str, issue_number: str) -> list[dict[str, Any]] | None:
    """Fetch comments for a GitHub issue.

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
        st.error(f"Error fetching comments: {e!s}")
        return None


def extract_comment_data(comment: dict[str, Any]) -> dict[str, Any]:
    """Extract relevant data from a comment.

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
    """Load issue data based on form input in the session state.

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
    form_issue_number = st.session_state.get("form_issue_number")
    if not form_issue_number or not str(form_issue_number).strip():
        return False

    # Check if we need to fetch new data
    if (
        st.session_state.get("issue_number") == st.session_state.form_issue_number
        and st.session_state.get("repo_info") == st.session_state.form_repo_info
        and "issue_data" in st.session_state
    ):
        return True

    with st.spinner(f"Fetching issue #{st.session_state.form_issue_number} from {st.session_state.form_repo_info}..."):
        # Fetch issue data
        issue_data = get_issue_data(
            st.session_state.form_repo_info,
            st.session_state.form_issue_number,
        )

        if issue_data:
            st.session_state.issue_data = issue_data
            st.session_state.issue_number = st.session_state.form_issue_number
            st.session_state.repo_info = st.session_state.form_repo_info
            st.success(f"Successfully fetched issue #{st.session_state.form_issue_number}")

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
                processed_comments = [extract_comment_data(comment) for comment in comments_data]
                st.session_state.processed_comments = processed_comments
            else:
                st.session_state.comments_data = []
                st.session_state.processed_comments = []

            return True
        st.error(
            f"Failed to fetch issue #{st.session_state.form_issue_number}. Please check the repository and issue number."
        )
        return False


@st.cache_data(ttl=60 * 15, max_entries=24)  # cache for 15 minutes
def get_all_github_issues(
    state: Literal["open", "closed", "all"] = "all",
    refresh_nonce: int = 0,
) -> list[dict[str, Any]]:
    """Paginate through all issues in the streamlit/streamlit repo.

    Returns all issues as a list of dicts.
    """
    _ = refresh_nonce  # Included to enable targeted cache busting from selected pages.
    issues = []
    state_param = f"state={state}" if state else ""
    url: str | None = f"https://api.github.com/repos/streamlit/streamlit/issues?{state_param}&per_page=100"

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
                st.error(f"Failed to retrieve data from {url}: {response.status_code}: {response.text}")
                break
        except Exception as ex:
            st.error(f"Failed to retrieve issues: {ex}")
            break
    return issues


@st.cache_data(ttl=60 * 15, max_entries=24)  # cache for 15 minutes
def get_all_github_prs(
    state: Literal["open", "closed", "all"] = "all",
    refresh_nonce: int = 0,
) -> list[dict[str, Any]]:
    """Paginate through all PRs in the streamlit/streamlit repo.

    Returns all PRs as a list of dicts.
    """
    _ = refresh_nonce  # Included to enable targeted cache busting from selected pages.
    prs = []
    state_param = f"state={state}" if state else ""
    url: str | None = f"https://api.github.com/repos/streamlit/streamlit/pulls?{state_param}&per_page=100"

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
                st.error(f"Failed to retrieve data from {url}: {response.status_code}: {response.text}")
                break
        except Exception as ex:
            st.error(f"Failed to retrieve PRs: {ex}")
            break
    return prs


@st.cache_data(ttl=60 * 60 * 24, show_spinner="Fetching workflow runs...")  # cache for 24 hours
def fetch_workflow_runs(
    workflow_name: str,
    limit: int = 50,
    since: date | None = None,
    branch: str | None = "develop",
    status: str | None = "success",
) -> list[dict[str, Any]]:
    """Fetch workflow runs for a specific workflow."""
    all_runs: list[dict[str, Any]] = []
    page = 1
    per_page = 100

    params: dict[str, Any] = {
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


@st.cache_data(ttl=60 * 60 * 6, max_entries=500, show_spinner="Fetching artifacts...")
def fetch_artifacts(run_id: int) -> list[dict[str, Any]]:
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


@st.cache_data(ttl=60 * 60 * 6, max_entries=500, show_spinner=False)
def download_artifact(artifact_url: str) -> bytes | None:
    """Download an artifact from GitHub Actions."""
    try:
        # The artifact URL is a redirect, so we need to get the real URL.
        redirect_response = requests.get(artifact_url, headers=get_headers(), timeout=60, allow_redirects=False)
        if redirect_response.status_code != 302:
            st.error(f"Error getting artifact redirect URL: {redirect_response.status_code}")
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


def zip_namelist(zip_bytes: bytes) -> list[str]:
    """Return the list of member names from a zip blob (in-memory)."""
    with ZipFile(BytesIO(zip_bytes)) as z:
        return z.namelist()


def iter_json_from_zip_bytes(
    zip_bytes: bytes, *, prefix: str | None = None, root_only: bool = False
) -> Iterator[tuple[str, Any]]:
    """Iterate JSON files within a zip blob (in-memory).

    Args:
        zip_bytes: Raw zip bytes.
        prefix: If provided, only consider members starting with this prefix.
        root_only: If True, only consider members at the zip root (no '/' in name).

    Yields:
        (member_name, parsed_json)
    """
    with ZipFile(BytesIO(zip_bytes)) as z:
        for name in z.namelist():
            if name.endswith("/"):
                continue
            if prefix is not None and not name.startswith(prefix):
                continue
            if root_only and "/" in name:
                continue
            if not name.endswith(".json"):
                continue
            with z.open(name) as f:
                yield name, json.load(f)


def first_json_from_zip_bytes(zip_bytes: bytes, *, prefix: str | None = None) -> tuple[str, Any] | None:
    """Return the first JSON member from a zip blob, optionally under a prefix."""
    for name, payload in iter_json_from_zip_bytes(zip_bytes, prefix=prefix):
        return name, payload
    return None


def fetch_pr_info(pr_number: str) -> dict[str, Any] | None:
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
def fetch_pr_reviews(pr_number: int) -> list[dict[str, Any]]:
    """Fetch all reviews for a given PR."""
    reviews: list[dict[str, Any]] = []
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
                st.error(f"Error fetching PR reviews for #{pr_number}: {response.status_code}")
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


def fetch_workflow_runs_for_commit(commit_sha: str, workflow_name: str) -> list[dict[str, Any]]:
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


@st.cache_data(ttl=60 * 60 * 6, max_entries=500, show_spinner=False)
def fetch_workflow_run_annotations(check_run_id: str) -> list[dict]:
    annotations_url = f"https://api.github.com/repos/streamlit/streamlit/check-runs/{check_run_id}/annotations"
    response = requests.get(annotations_url, headers=get_headers(), timeout=30)

    if response.status_code == 200:
        return response.json()
    st.error(f"Error fetching annotations: {response.status_code}")
    return []


@st.cache_data(ttl=60 * 60 * 6, max_entries=500, show_spinner=False)
def fetch_workflow_runs_ids(check_suite_id: str) -> list[str]:
    annotations_url = f"https://api.github.com/repos/streamlit/streamlit/check-suites/{check_suite_id}/check-runs"
    response = requests.get(annotations_url, headers=get_headers(), timeout=30)

    if response.status_code == 200:
        check_runs = response.json()["check_runs"]
        check_runs = [check_run for check_run in check_runs if check_run["conclusion"] == "success"]
        return [check_run["id"] for check_run in check_runs]
    st.error(f"Error fetching annotations: {response.status_code}")
    return []


def extract_issue_number(github_url: str) -> int:
    """Extract issue number from GitHub URL."""
    if "/issues/" in github_url:
        try:
            return int(github_url.rsplit("/issues/", maxsplit=1)[-1].split("?")[0].split("#")[0])
        except (ValueError, IndexError):
            return 0
    return 0


def validate_issue_number(issue_str: str) -> tuple[bool, int | None]:
    """Validate issue number is between 1 and 150,000."""
    try:
        issue_num = int(issue_str.strip())
        if 1 <= issue_num <= 150000:
            return True, issue_num
        return False, None
    except (ValueError, TypeError):
        return False, None


def parse_github_url(url: str | None) -> tuple[str | None, str | None]:
    """Parse GitHub issue URL to extract repository and issue number."""
    import re

    if not url or not url.strip():
        return None, None

    url = url.strip()

    # Remove @ symbol if present at the beginning
    url = url.removeprefix("@")

    # Pattern to match GitHub issue URLs
    pattern = r"https://github\.com/([^/]+/[^/]+)/issues/(\d+)"
    match = re.match(pattern, url)

    if match:
        repo_info = match.group(1)
        issue_number = match.group(2)
        return repo_info, issue_number

    return None, None


@st.cache_data(ttl=60 * 60 * 6)  # cache for 6 hours
def get_count_issues_commented_by_user(username: str, _repo: str = "streamlit/streamlit") -> int:
    """Get the number of issues commented on by a user."""
    headers = get_headers()
    query = f"repo:streamlit/streamlit is:issue commenter:{username}"
    # Manually encode the query to ensure compatibility
    # safe="" ensures that slashes are also encoded
    encoded_query = urllib.parse.quote(query, safe="")
    url = f"https://api.github.com/search/issues?q={encoded_query}&per_page=1"

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json().get("total_count", 0)
    except Exception as e:
        st.error(f"Error fetching commented issues count for {username}: {e}")
        with contextlib.suppress(Exception):
            # Try to show the error message from GitHub
            st.error(f"GitHub API Error: {response.text}")
        return 0
