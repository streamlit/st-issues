from typing import Any

from app.utils.ai.template_loader import render_template


def generate_debugging_prompt(
    issue_title: str, issue_body: str, comments: list[dict[str, Any]] | None = None
) -> dict[str, str]:
    """Generates a prompt for an AI Agent to help identify the root cause of a bug.

    Args:
        issue_title: The title of the GitHub issue
        issue_body: The body/description of the GitHub issue
        comments: Optional list of comment data from the issue

    Returns:
        Dict containing the prompt and related metadata
    """
    # Filter out bot comments if comments are provided
    filtered_comments = None
    if comments:
        filtered_comments = [comment for comment in comments if comment.get("author") != "github-actions[bot]"]
        # Only pass non-empty filtered comments to template
        if not filtered_comments:
            filtered_comments = None

    # Render the template with the provided context
    prompt = render_template(
        "debugging_prompt.j2",
        issue_title=issue_title,
        issue_body=issue_body,
        comments=filtered_comments,
    )

    return {"prompt": prompt, "issue_title": issue_title, "prompt_type": "debugging"}


def generate_workaround_prompt(
    issue_title: str, issue_body: str, comments: list[dict[str, Any]] | None = None
) -> dict[str, str]:
    """Generates a prompt for an AI Agent to help suggest workarounds for Streamlit issues.

    Args:
        issue_title: The title of the GitHub issue
        issue_body: The body/description of the GitHub issue
        comments: Optional list of comment data from the issue

    Returns:
        Dict containing the prompt and related metadata
    """
    # Filter out bot comments if comments are provided
    filtered_comments = None
    if comments:
        filtered_comments = [comment for comment in comments if comment.get("author") != "github-actions[bot]"]
        # Only pass non-empty filtered comments to template
        if not filtered_comments:
            filtered_comments = None

    # Render the template with the provided context
    prompt = render_template(
        "workaround_prompt.j2",
        issue_title=issue_title,
        issue_body=issue_body,
        comments=filtered_comments,
    )

    return {"prompt": prompt, "issue_title": issue_title, "prompt_type": "workaround"}
