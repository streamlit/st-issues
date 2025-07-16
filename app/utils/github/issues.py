from typing import Any, Dict, List, Optional

import requests
import streamlit as st


def get_headers(token: str):
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def get_issue_data(
    repo: str, issue_number: str, token: str
) -> Optional[Dict[str, Any]]:
    """
    Fetch issue data from GitHub API

    Args:
        repo: Repository in format "owner/repo"
        issue_number: Issue number
        token: GitHub API token

    Returns:
        Dictionary containing issue data or None if request fails
    """
    headers = get_headers(token)
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"

    try:
        response = requests.get(url, headers=headers)
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


def get_issue_comments(
    repo: str, issue_number: str, token: str
) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch comments for a GitHub issue

    Args:
        repo: Repository in format "owner/repo"
        issue_number: Issue number
        token: GitHub API token

    Returns:
        List of comments or None if request fails
    """
    headers = get_headers(token)
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"

    try:
        response = requests.get(url, headers=headers)
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
