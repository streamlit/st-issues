from typing import Any, Dict, List, Optional


def generate_debugging_prompt(
    issue_title: str, issue_body: str, comments: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, str]:
    """
    Generates a prompt for Cursor AI to help identify the root cause of a bug.

    Args:
        issue_title: The title of the GitHub issue
        issue_body: The body/description of the GitHub issue
        comments: Optional list of comment data from the issue

    Returns:
        Dict containing the prompt and related metadata
    """
    # Base context about investigating Streamlit issues
    base_context = """
You are helping me debug an issue in the Streamlit repository. I need your help identifying the most likely root cause of a user-reported issue.

Your task is to deeply analyze the issue description and any available comments, then search through the codebase to identify the most probable cause of the problem. Don't focus on fixing the issue yet, but provide a thorough analysis of what's likely going wrong.
"""

    # Format the issue information
    issue_info = (
        f"## Issue Title:\n{issue_title}\n\n## Issue Description:\n{issue_body}\n\n"
    )

    # Add comments if provided
    comments_text = ""
    if comments:  # Check if comments is not None
        filtered_comments = [
            comment
            for comment in comments
            if comment.get("author") != "github-actions[bot]"
        ]
        if filtered_comments and len(filtered_comments) > 0:
            comments_text = "## Comments:\n"
            for comment in filtered_comments:
                comments_text += f"**{comment.get('author', 'Unknown')}** wrote:\n{comment.get('body', '')}\n\n"

    # Instructions for the AI
    instructions = """
## Your Task:
1. Thoroughly analyze the issue description and comments
2. Identify the specific component(s) of Streamlit that are likely involved
3. Search through relevant code files to find potential problematic sections
4. Provide a detailed analysis of what's likely causing the issue, including:
   - The specific code path that's being triggered
   - How inputs or state might be causing unexpected behavior
   - Any edge cases that might not be handled properly
   - How the observed behavior differs from expected behavior
5. Consider various factors like browser compatibility, operating system specifics, or version-specific issues
6. Explain your reasoning step by step, citing specific parts of the codebase where appropriate

Focus on identifying the root cause with high confidence rather than proposing fixes at this stage.
"""

    # Combine all parts to create the final prompt
    prompt = f"{base_context}\n\n{issue_info}\n{comments_text}\n{instructions}"

    return {"prompt": prompt, "issue_title": issue_title, "prompt_type": "debugging"}


def generate_workaround_prompt(
    issue_title: str, issue_body: str, comments: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, str]:
    """
    Generates a prompt for Cursor AI to help suggest workarounds for Streamlit issues.

    Args:
        issue_title: The title of the GitHub issue
        issue_body: The body/description of the GitHub issue
        comments: Optional list of comment data from the issue

    Returns:
        Dict containing the prompt and related metadata
    """
    # Base context about suggesting workarounds for Streamlit issues
    base_context = """
You are helping a user with an issue they're experiencing in their Streamlit application. The user has reported a problem, and
while the root cause might be in the Streamlit framework itself, we want to provide them with a temporary workaround they can
implement in their own code while the issue is being addressed by the Streamlit team.

You'll need to analyze the issue carefully to understand what the user is trying to accomplish and what's going wrong.
"""

    # Format the issue information
    issue_info = (
        f"## Issue Title:\n{issue_title}\n\n## Issue Description:\n{issue_body}\n\n"
    )

    # Add comments if provided
    comments_text = ""
    if comments:  # Check if comments is not None
        filtered_comments = [
            comment
            for comment in comments
            if comment.get("author") != "github-actions[bot]"
        ]
        if filtered_comments and len(filtered_comments) > 0:
            comments_text = "## Comments:\n"
            for comment in filtered_comments:
                comments_text += f"**{comment.get('author', 'Unknown')}** wrote:\n{comment.get('body', '')}\n\n"

    # Instructions for the AI
    instructions = """
## Your Task:
1. Analyze the issue to understand what functionality the user is trying to implement
2. Identify the specific problem they're encountering
3. Suggest one or more practical workarounds that the user could implement in their own code
4. For each workaround:
   - Provide clear, copy-pastable code examples
   - Explain how the workaround addresses the issue
   - Note any limitations or edge cases the workaround might have
5. Focus on solutions that the user can implement immediately without changes to Streamlit itself
6. If relevant, explain why this issue might be happening (briefly)

Make your suggestions practical and ready to use, focusing on helping the user continue development while the core issue is addressed.
"""

    # Combine all parts to create the final prompt
    prompt = f"{base_context}\n\n{issue_info}\n{comments_text}\n{instructions}"

    return {"prompt": prompt, "issue_title": issue_title, "prompt_type": "workaround"}
