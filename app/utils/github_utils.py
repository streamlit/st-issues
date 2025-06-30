from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Literal, Optional

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

GITHUB_API_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token {st.secrets['github']['token']}",
}


def is_community_author(author: str) -> bool:
    """Check if an author is a community member."""
    return (
        author not in STREAMLIT_TEAM_MEMBERS
        and not author.startswith("sfc-gh-")
        and not author.endswith("[bot]")
    )


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
                headers=GITHUB_API_HEADERS,
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
                headers=GITHUB_API_HEADERS,
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
                headers=GITHUB_API_HEADERS,
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
            headers=GITHUB_API_HEADERS,
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
            artifact_url, headers=GITHUB_API_HEADERS, timeout=60, allow_redirects=False
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
            headers=GITHUB_API_HEADERS,
            timeout=30,
        )

        if response.status_code != 200:
            st.error(f"Error fetching PR info: {response.status_code}")
            return None

        return response.json()
    except Exception as e:
        st.error(f"Error fetching PR info: {e}")
        return None


def fetch_workflow_runs_for_commit(
    commit_sha: str, workflow_name: str
) -> List[Dict[str, Any]]:
    """Fetch workflow runs for a specific commit."""
    try:
        response = requests.get(
            f"https://api.github.com/repos/streamlit/streamlit/actions/workflows/{workflow_name}/runs?head_sha={commit_sha}&status=success",
            headers=GITHUB_API_HEADERS,
            timeout=30,
        )

        if response.status_code != 200:
            st.error(f"Error fetching workflow runs for commit: {response.status_code}")
            return []

        return response.json().get("workflow_runs", [])
    except Exception as e:
        st.error(f"Error fetching workflow runs for commit: {e}")
        return []


@st.cache_data(ttl=60 * 5)  # cache for 5 minutes
def get_github_issue(issue_number: str) -> dict:
    """Request a single issue from GitHub API."""
    try:
        response = requests.get(
            f"https://api.github.com/repos/streamlit/streamlit/issues/{issue_number}",
            headers=GITHUB_API_HEADERS,
            timeout=100,
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to retrieve data: {response.status_code}")
    except Exception as ex:
        st.error(f"Failed to retrieve issue: {ex}")
    return {}


@st.cache_data(show_spinner=False)
def fetch_workflow_run_annotations(check_run_id: str) -> list[dict]:
    annotations_url = f"https://api.github.com/repos/streamlit/streamlit/check-runs/{check_run_id}/annotations"
    response = requests.get(annotations_url, headers=GITHUB_API_HEADERS)

    if response.status_code == 200:
        return response.json()
    st.error(f"Error fetching annotations: {response.status_code}")
    return []


@st.cache_data(show_spinner=False)
def fetch_workflow_runs_ids(check_suite_id: str) -> list[str]:
    annotations_url = f"https://api.github.com/repos/streamlit/streamlit/check-suites/{check_suite_id}/check-runs"
    response = requests.get(annotations_url, headers=GITHUB_API_HEADERS)

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
