from __future__ import annotations

import re
from typing import TypedDict

import requests
import streamlit as st

DEFAULT_GITHUB_REPO = "streamlit/streamlit"


class IssuePreviewDetails(TypedDict):
    title: str
    url: str
    state: str
    number: int
    upvotes: int


def _get_optional_github_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}

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


@st.cache_data(ttl=300, max_entries=512, show_spinner=False)
def fetch_issue_preview_details(repo: str, issue_number: int) -> tuple[IssuePreviewDetails | None, str | None]:
    """Fetch issue details used for markdown issue previews."""
    try:
        response = requests.get(
            f"https://api.github.com/repos/{repo}/issues/{issue_number}",
            headers=_get_optional_github_headers(),
            timeout=30,
        )
    except requests.RequestException:
        return None, None

    if response.status_code == 404:
        return None, None
    if response.status_code != 200:
        return None, None

    try:
        issue_data = response.json()
    except ValueError:
        return None, None

    if not isinstance(issue_data, dict):
        return None, None

    return {
        "title": issue_data["title"],
        "url": issue_data["html_url"],
        "state": issue_data["state"],
        "number": issue_data["number"],
        "upvotes": issue_data.get("reactions", {}).get("+1", 0),
    }, None


def sanitize_title_for_markdown_link(title: str) -> str:
    """Remove markdown-breaking characters from issue titles used in links."""
    sanitized_title = title.replace("`", "")
    return sanitized_title.replace("[", "(").replace("]", ")")


def replace_issue_references_with_previews(
    markdown_content: str,
    *,
    repo: str = DEFAULT_GITHUB_REPO,
) -> str:
    """Replace issue references with styled previews."""
    escaped_repo = re.escape(repo)
    link_pattern = rf"\[#(\d+)\]\(https://github\.com/{escaped_repo}/issues/\d+[^)]*\)"
    standalone_pattern = r"(?<!\[)#(\d+)(?![\]\(])"

    def create_issue_preview(issue_number: int) -> str:
        issue_details, _error = fetch_issue_preview_details(repo, issue_number)
        if not issue_details:
            return f"#{issue_number}"

        status_icon = (
            ":green[:material/circle:]" if issue_details["state"] == "open" else ":violet[:material/check_circle:]"
        )

        title = sanitize_title_for_markdown_link(issue_details["title"])
        if len(title) > 50:
            title = title[:50] + "..."

        upvotes_badge = f":orange-badge[{issue_details['upvotes']} :material/thumb_up:]"
        return f"{status_icon} :gray[#{issue_details['number']}] [{title}]({issue_details['url']}) {upvotes_badge}"

    def replace_issue_link(match: re.Match[str]) -> str:
        return create_issue_preview(int(match.group(1)))

    def replace_standalone_issue(match: re.Match[str]) -> str:
        return create_issue_preview(int(match.group(1)))

    updated_content = re.sub(link_pattern, replace_issue_link, markdown_content)
    return re.sub(standalone_pattern, replace_standalone_issue, updated_content)
