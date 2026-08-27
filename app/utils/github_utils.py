from __future__ import annotations

import base64
import contextlib
import json
import urllib.parse
from datetime import UTC, date, datetime
from io import BytesIO
from typing import TYPE_CHECKING, Any, Final, Literal, Protocol, cast
from zipfile import ZipFile

import requests
import streamlit as st

from app.utils.github_graphql_utils import _run_graphql_query

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

# Streamlit team members:

ACTIVE_STREAMLIT_TEAM_MEMBERS = [
    "lukasmasuch",
    "kmcgrady",
    "mayagbarnes",
    "jrieke",
    "sfc-gh-lwilby",
    "sfc-gh-lwilby-1",
    "sfc-gh-bnisco",
    "sfc-gh-nbellante",
    "sfc-gh-tteixeira",
    "sfc-gh-dmatthews",
    "sfc-gh-lmasuch",
]

STREAMLIT_TEAM_MEMBERS = [
    *ACTIVE_STREAMLIT_TEAM_MEMBERS,
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
    """Get headers for GitHub API requests with optional auth."""
    headers = {"Accept": "application/vnd.github.v3+json"}

    try:
        github_secrets = st.secrets.get("github")
    except Exception:
        github_secrets = None

    if github_secrets is not None:
        try:
            token = github_secrets.get("token")
        except Exception:
            token = None
        if isinstance(token, str) and token:
            headers["Authorization"] = f"token {token}"

    return headers


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


class _PullRequestFilesPayloadFetcher(Protocol):
    def __call__(self, repo: str, pr_number: int) -> tuple[list[dict[str, Any]], str | None]: ...

    clear: Callable[..., None]


@st.cache_data(ttl=60 * 10, max_entries=256, show_spinner=False, refresh_mode="background")
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


@st.cache_data(ttl=60 * 10, max_entries=256, show_spinner=False, refresh_mode="background")
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


@st.cache_data(ttl=60 * 60, max_entries=1024, show_spinner=False, refresh_mode="background")
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


@st.cache_data(ttl=60 * 60, max_entries=2048, show_spinner=False, refresh_mode="background")
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


@st.cache_data(ttl=60 * 60, max_entries=256, show_spinner=False, refresh_mode="background")
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


@st.cache_data(ttl=300, max_entries=256, show_spinner=False, refresh_mode="background")
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


@st.cache_data(ttl=300, max_entries=256, show_spinner=False, refresh_mode="background")
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


def _fetch_pull_request_files_payload(repo: str, pr_number: int) -> tuple[list[dict[str, Any]], str | None]:
    """Fetch all changed files for a pull request."""
    try:
        return _fetch_pull_request_files_payload_cached(repo, pr_number), None
    except _PartialDataError as exc:
        return cast("list[dict[str, Any]]", exc.partial_data), str(exc)


fetch_pull_request_files_payload = cast("_PullRequestFilesPayloadFetcher", _fetch_pull_request_files_payload)
fetch_pull_request_files_payload.clear = _fetch_pull_request_files_payload_cached.clear


@st.cache_data(ttl=300, max_entries=256, show_spinner=False, refresh_mode="background")
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


@st.cache_data(ttl=60 * 60 * 12, max_entries=128, show_spinner=False, refresh_mode="background")
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


@st.cache_data(ttl=60 * 5, refresh_mode="background")  # cache for 5 minutes
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


@st.cache_data(ttl=60 * 5, refresh_mode="background")  # cache for 5 minutes
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


@st.cache_data(ttl=60 * 15, max_entries=24, refresh_mode="background")  # cache for 15 minutes
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


@st.cache_data(ttl=60 * 15, max_entries=128, refresh_mode="background")  # cache for 15 minutes
def get_all_github_prs(
    state: Literal["open", "closed", "all"] = "all",
    refresh_nonce: int = 0,
    repo: str = "streamlit/streamlit",
) -> list[dict[str, Any]]:
    """Paginate through all PRs in a GitHub repo.

    Returns all PRs as a list of dicts.
    """
    _ = refresh_nonce  # Included to enable targeted cache busting from selected pages.
    prs = []
    state_param = f"state={state}" if state else ""
    url: str | None = f"https://api.github.com/repos/{repo}/pulls?{state_param}&per_page=100"

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


# GitHub's REST workflow-run filters (`branch`, `status`, `created`) go through a
# search index that can return a stale first page. GraphQL `Workflow.runs` ordered
# by `CREATED_AT DESC` is current; branch/status/`since` are applied locally.
_WORKFLOW_RUNS_PAGE_SIZE: Final[int] = 100
_WORKFLOW_RUNS_MAX_PAGES: Final[int] = 80
_CHECK_CONTEXTS_PAGE_SIZE: Final[int] = 100
_CHECK_CONTEXTS_MAX_PAGES: Final[int] = 10
_WORKFLOW_CONCLUSION_FILTERS: Final[frozenset[str]] = frozenset(
    {
        "success",
        "failure",
        "cancelled",
        "canceled",
        "skipped",
        "timed_out",
        "action_required",
        "neutral",
        "stale",
        "startup_failure",
    }
)
_WORKFLOW_STATUS_FILTERS: Final[frozenset[str]] = frozenset(
    {
        "completed",
        "in_progress",
        "queued",
        "waiting",
        "pending",
        "requested",
    }
)
_WORKFLOW_RUNS_QUERY: Final[str] = """
query($workflowId: ID!, $cursor: String, $pageSize: Int!) {
  node(id: $workflowId) {
    ... on Workflow {
      runs(
        first: $pageSize
        after: $cursor
        orderBy: {field: CREATED_AT, direction: DESC}
      ) {
        nodes {
          databaseId
          createdAt
          event
          url
          checkSuite {
            databaseId
            status
            conclusion
            branch { name }
            commit { oid }
          }
        }
        pageInfo {
          endCursor
          hasNextPage
        }
      }
    }
  }
}
"""


def _get_workflow_node_id(workflow_name: str) -> str | None:
    """Resolve a workflow file name to the GraphQL node ID via REST."""
    payload, error, _status = _request_json(
        f"https://api.github.com/repos/streamlit/streamlit/actions/workflows/{workflow_name}",
    )
    if error or not isinstance(payload, dict):
        st.error(error or f"Unexpected workflow payload for {workflow_name}.")
        return None
    node_id = payload.get("node_id")
    if not isinstance(node_id, str) or not node_id:
        st.error(f"Workflow {workflow_name} is missing a GraphQL node ID.")
        return None
    return node_id


def _enum_lower(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return value.lower()


def _to_rest_timestamp(value: object) -> str | None:
    """Normalize a GraphQL DateTime to the REST `YYYY-MM-DDTHH:MM:SSZ` form."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value).astimezone(UTC)
    except ValueError:
        return None
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_run_created_at(created_at: str) -> datetime:
    return datetime.fromisoformat(created_at).astimezone(UTC).replace(tzinfo=None)


def _since_cutoff(since: date | datetime) -> datetime:
    # `datetime` is a `date` subclass, so check it first.
    if isinstance(since, datetime):
        if since.tzinfo is None:
            return since
        return since.astimezone(UTC).replace(tzinfo=None)
    return datetime.combine(since, datetime.min.time())


def _graphql_workflow_run_to_rest(node: dict[str, Any]) -> dict[str, Any] | None:
    """Map a GraphQL WorkflowRun node to the REST workflow-run fields callers use."""
    run_id = node.get("databaseId")
    check_suite = node.get("checkSuite") or {}
    if not isinstance(check_suite, dict):
        check_suite = {}
    commit = check_suite.get("commit") or {}
    branch = check_suite.get("branch") or {}
    head_sha = commit.get("oid") if isinstance(commit, dict) else None
    created_at = _to_rest_timestamp(node.get("createdAt"))
    if not isinstance(run_id, int) or not isinstance(head_sha, str) or not head_sha or created_at is None:
        return None

    html_url = node.get("url")
    if not isinstance(html_url, str) or not html_url:
        html_url = f"https://github.com/streamlit/streamlit/actions/runs/{run_id}"

    head_branch = branch.get("name") if isinstance(branch, dict) else None
    return {
        "id": run_id,
        "head_sha": head_sha,
        "created_at": created_at,
        "html_url": html_url,
        "check_suite_id": check_suite.get("databaseId"),
        "status": _enum_lower(check_suite.get("status")),
        "conclusion": _enum_lower(check_suite.get("conclusion")),
        "head_branch": head_branch if isinstance(head_branch, str) else None,
        "event": node.get("event"),
    }


def _workflow_run_matches(
    run: dict[str, Any],
    *,
    branch: str | None,
    status: str | None,
) -> bool:
    if branch and run.get("head_branch") != branch:
        return False
    if not status:
        return True
    wanted = status.lower()
    conclusion = run.get("conclusion")
    run_status = run.get("status")
    if wanted == "canceled":
        wanted = "cancelled"
    if wanted in _WORKFLOW_CONCLUSION_FILTERS:
        return conclusion == wanted
    if wanted in _WORKFLOW_STATUS_FILTERS:
        return run_status == wanted
    return wanted in {conclusion, run_status}


@st.cache_data(ttl=60 * 10, max_entries=32, show_spinner=False, refresh_mode="background")
def fetch_commit_shas(branch: str = "develop", limit: int = 10, refresh_nonce: int = 0) -> list[str]:
    """Fetch the newest commit SHAs for a branch, newest first."""
    _ = refresh_nonce  # Included to enable targeted cache busting from selected pages.
    payload, error, _status = _request_json(
        "https://api.github.com/repos/streamlit/streamlit/commits",
        params={"sha": branch, "per_page": min(limit, 100)},
    )
    if error:
        st.error(error)
        return []
    if not isinstance(payload, list):
        st.error(f"Unexpected commits payload for {branch}.")
        return []

    shas: list[str] = []
    for commit in payload:
        if not isinstance(commit, dict):
            continue
        sha = commit.get("sha")
        if isinstance(sha, str) and sha:
            shas.append(sha)
    return shas


_CHECK_CONTEXT_FIELDS: Final[str] = """
fragment CheckContextFields on StatusCheckRollupContext {
  __typename
  ... on CheckRun {
    name
    status
    conclusion
  }
  ... on StatusContext {
    context
    state
  }
}
"""
_DEVELOP_COMMIT_CHECKS_QUERY: Final[str] = (
    _CHECK_CONTEXT_FIELDS
    + """
query($historyFirst: Int!, $contextsFirst: Int!) {
  repository(owner: "streamlit", name: "streamlit") {
    ref(qualifiedName: "refs/heads/develop") {
      target {
        ... on Commit {
          history(first: $historyFirst) {
            nodes {
              oid
              statusCheckRollup {
                contexts(first: $contextsFirst) {
                  pageInfo {
                    hasNextPage
                    endCursor
                  }
                  nodes {
                    ...CheckContextFields
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""
)
_COMMIT_CHECK_CONTEXTS_QUERY: Final[str] = (
    _CHECK_CONTEXT_FIELDS
    + """
query($oid: GitObjectID!, $contextsFirst: Int!, $cursor: String) {
  repository(owner: "streamlit", name: "streamlit") {
    object(oid: $oid) {
      ... on Commit {
        statusCheckRollup {
          contexts(first: $contextsFirst, after: $cursor) {
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              ...CheckContextFields
            }
          }
        }
      }
    }
  }
}
"""
)


def _normalize_check_context(node: dict[str, Any]) -> dict[str, Any] | None:
    """Map a GraphQL check-rollup context to a uniform check dict."""
    typename = node.get("__typename")
    if typename == "CheckRun" or (typename is None and "conclusion" in node):
        name = node.get("name")
        if not isinstance(name, str) or not name:
            return None
        return {
            "name": name,
            "kind": "check_run",
            "status": _enum_lower(node.get("status")),
            "conclusion": _enum_lower(node.get("conclusion")),
            "state": None,
        }
    if typename == "StatusContext" or (typename is None and "state" in node):
        name = node.get("context")
        if not isinstance(name, str) or not name:
            return None
        return {
            "name": name,
            "kind": "status",
            "status": None,
            "conclusion": None,
            "state": _enum_lower(node.get("state")),
        }
    return None


def _parse_check_contexts_connection(
    connection: dict[str, Any],
) -> tuple[list[dict[str, Any]], str | None, bool]:
    """Return (checks, end_cursor, has_next_page) for a rollup contexts connection."""
    checks: list[dict[str, Any]] = []
    for node in connection.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        parsed = _normalize_check_context(node)
        if parsed is not None:
            checks.append(parsed)
    page_info = connection.get("pageInfo") or {}
    end_cursor = page_info.get("endCursor")
    has_next = bool(page_info.get("hasNextPage"))
    if not isinstance(end_cursor, str) or not end_cursor:
        end_cursor = None
        has_next = False
    return checks, end_cursor, has_next


def _fetch_remaining_check_contexts(oid: str, cursor: str) -> list[dict[str, Any]]:
    """Paginate remaining status-check rollup contexts for one commit."""
    checks: list[dict[str, Any]] = []
    next_cursor: str | None = cursor
    for _page in range(_CHECK_CONTEXTS_MAX_PAGES - 1):
        if next_cursor is None:
            break
        try:
            data = _run_graphql_query(
                _COMMIT_CHECK_CONTEXTS_QUERY,
                {
                    "oid": oid,
                    "contextsFirst": _CHECK_CONTEXTS_PAGE_SIZE,
                    "cursor": next_cursor,
                },
            )
        except Exception as exc:
            st.error(f"Error fetching commit checks: {exc}")
            break
        repo = data.get("repository") or {}
        obj = repo.get("object") or {}
        rollup = obj.get("statusCheckRollup") or {}
        page_checks, next_cursor, has_next = _parse_check_contexts_connection(rollup.get("contexts") or {})
        checks.extend(page_checks)
        if not has_next:
            break
    return checks


@st.cache_data(ttl=60 * 10, max_entries=32, show_spinner=False, refresh_mode="background")
def fetch_develop_commit_checks(limit: int = 10, refresh_nonce: int = 0) -> list[dict[str, Any]]:
    """Fetch GitHub checks for the newest commits on `develop`, newest first.

    Each item is `{"sha": str, "checks": list[dict]}` covering CheckRun and
    StatusContext entries from `statusCheckRollup`.
    """
    _ = refresh_nonce  # Included to enable targeted cache busting from selected pages.
    try:
        data = _run_graphql_query(
            _DEVELOP_COMMIT_CHECKS_QUERY,
            {
                "historyFirst": min(limit, 100),
                "contextsFirst": _CHECK_CONTEXTS_PAGE_SIZE,
            },
        )
    except Exception as exc:
        st.error(f"Error fetching commit checks: {exc}")
        return []

    repo = data.get("repository") or {}
    ref = repo.get("ref")
    if not isinstance(ref, dict):
        st.error("GraphQL did not return the develop ref.")
        return []
    target = ref.get("target") or {}
    history = target.get("history") or {}
    commits: list[dict[str, Any]] = []
    for node in history.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        sha = node.get("oid")
        if not isinstance(sha, str) or not sha:
            continue
        rollup = node.get("statusCheckRollup") or {}
        checks, cursor, has_next = _parse_check_contexts_connection(rollup.get("contexts") or {})
        if has_next and cursor is not None:
            checks.extend(_fetch_remaining_check_contexts(sha, cursor))
        commits.append({"sha": sha, "checks": checks})
    return commits[:limit]


@st.cache_data(
    ttl=60 * 60 * 24, show_spinner="Fetching workflow runs...", refresh_mode="background"
)  # cache for 24 hours
def fetch_workflow_runs(
    workflow_name: str,
    limit: int = 50,
    since: date | datetime | None = None,
    branch: str | None = "develop",
    status: str | None = "success",
) -> list[dict[str, Any]]:
    """Fetch workflow runs for a specific workflow, newest first.

    Uses GraphQL `CREATED_AT DESC` instead of REST `branch`/`status` filters, which
    can return a stale first page. Results are still shaped like REST workflow runs
    (`id`, `head_sha`, `created_at`, `html_url`, `check_suite_id`, `status`,
    `conclusion`, `head_branch`, `event`).
    """
    workflow_node_id = _get_workflow_node_id(workflow_name)
    if workflow_node_id is None:
        return []

    cutoff = _since_cutoff(since) if since is not None else None
    matching_runs: list[dict[str, Any]] = []
    cursor: str | None = None

    for _page in range(_WORKFLOW_RUNS_MAX_PAGES):
        try:
            data = _run_graphql_query(
                _WORKFLOW_RUNS_QUERY,
                {
                    "workflowId": workflow_node_id,
                    "cursor": cursor,
                    "pageSize": _WORKFLOW_RUNS_PAGE_SIZE,
                },
            )
        except Exception as exc:
            st.error(f"Error fetching workflow runs: {exc}")
            break

        workflow = data.get("node")
        if not isinstance(workflow, dict):
            st.error(f"GraphQL did not return runs for workflow {workflow_name}.")
            break

        connection = workflow.get("runs") or {}
        reached_since_bound = False
        for raw_node in connection.get("nodes") or []:
            if not isinstance(raw_node, dict):
                continue
            run = _graphql_workflow_run_to_rest(raw_node)
            if run is None:
                continue
            if cutoff is not None and _parse_run_created_at(run["created_at"]) < cutoff:
                reached_since_bound = True
                break
            if not _workflow_run_matches(run, branch=branch, status=status):
                continue
            matching_runs.append(run)
            if len(matching_runs) >= limit:
                return matching_runs[:limit]

        if reached_since_bound:
            break

        page_info = connection.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        next_cursor = page_info.get("endCursor")
        if not isinstance(next_cursor, str) or not next_cursor:
            break
        cursor = next_cursor

    return matching_runs[:limit]


@st.cache_data(ttl=60 * 60 * 6, max_entries=500, show_spinner="Fetching artifacts...", refresh_mode="background")
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


@st.cache_data(ttl=60 * 60 * 6, max_entries=500, show_spinner=False, refresh_mode="background")
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


@st.cache_data(ttl=60 * 60 * 3, show_spinner=False, refresh_mode="background")
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


@st.cache_data(ttl=60 * 60 * 6, max_entries=500, show_spinner=False, refresh_mode="background")
def fetch_workflow_run_annotations(check_run_id: str) -> list[dict]:
    annotations_url = f"https://api.github.com/repos/streamlit/streamlit/check-runs/{check_run_id}/annotations"
    response = requests.get(annotations_url, headers=get_headers(), timeout=30)

    if response.status_code == 200:
        return response.json()
    st.error(f"Error fetching annotations: {response.status_code}")
    return []


@st.cache_data(ttl=60 * 60 * 6, max_entries=500, show_spinner=False, refresh_mode="background")
def fetch_workflow_runs_ids(check_suite_id: str) -> list[str]:
    annotations_url = f"https://api.github.com/repos/streamlit/streamlit/check-suites/{check_suite_id}/check-runs"
    response = requests.get(annotations_url, headers=get_headers(), timeout=30)

    if response.status_code == 200:
        check_runs = response.json()["check_runs"]
        check_runs = [check_run for check_run in check_runs if check_run["conclusion"] == "success"]
        return [check_run["id"] for check_run in check_runs]
    st.error(f"Error fetching annotations: {response.status_code}")
    return []


@st.cache_data(ttl=60 * 60 * 6, refresh_mode="background")  # cache for 6 hours
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
