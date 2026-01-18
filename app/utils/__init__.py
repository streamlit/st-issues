from typing import Any

import streamlit as st


def display_issue_data() -> bool:
    """Display issue data if available in session state.

    Returns True if issue data was displayed, False otherwise.
    """
    if "issue_data" not in st.session_state:
        # Show form to load issue data
        st.subheader("Load GitHub Issue")

        with st.form("issue_form"):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.text_input("Repository", value="streamlit/streamlit", key="form_repo_info")

            with col2:
                st.text_input("Issue Number", key="form_issue_number")

            st.form_submit_button("Load Issue")

        return False

    # Display issue metadata if available
    if "issue_metadata" in st.session_state:
        metadata = st.session_state.issue_metadata

        with st.expander("Issue Details", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Title:** {metadata.get('title', 'N/A')}")
                st.markdown(f"**Number:** #{metadata.get('number', 'N/A')}")
                st.markdown(f"**State:** {metadata.get('state', 'N/A')}")
                st.markdown(f"**Author:** {metadata.get('author', 'N/A')}")

            with col2:
                st.markdown(f"**Created:** {metadata.get('created_at', 'N/A')}")
                st.markdown(f"**Updated:** {metadata.get('updated_at', 'N/A')}")
                st.markdown(f"**Labels:** {', '.join(metadata.get('labels', []))}")

                if metadata.get("html_url"):
                    st.markdown(f"**URL:** [View on GitHub]({metadata.get('html_url')})")

            # Display issue body
            if metadata.get("body"):
                st.markdown("**Description:**")
                st.markdown(metadata.get("body"))

        # Display comments if available
        if "processed_comments" in st.session_state and st.session_state.processed_comments:
            with st.expander(f"Comments ({len(st.session_state.processed_comments)})", expanded=False):
                for comment in st.session_state.processed_comments:
                    st.markdown(f"**{comment.get('author', 'Unknown')}** - {comment.get('created_at', '')}")
                    st.markdown(comment.get("body", ""))
                    st.markdown("---")

        return True

    return False


def display_agent_prompt(prompt_data: dict[str, Any]) -> None:
    """Display the generated agent prompt with copy functionality.

    Args:
        prompt_data: Dictionary containing prompt and metadata
    """
    if not prompt_data:
        st.error("No prompt data provided")
        return

    # Display the prompt in a code block for easy copying
    if "prompt" in prompt_data:
        st.markdown(
            """### Copy this prompt to your Agent:

💡 **Tip:** Click the copy button in the top-right corner of the code block to copy the prompt to your clipboard."""
        )

        st.code(prompt_data["prompt"], language=None)
    else:
        st.error("No prompt found in prompt data")


def load_issue_from_metadata(issue_metadata: dict[str, Any], repo: str = "streamlit/streamlit") -> None:
    """Load issue data from issue metadata (used for integration with interrupt rotation).

    Args:
        issue_metadata: Dictionary containing issue metadata
        repo: Repository in format "owner/repo"
    """
    from app.utils.github_utils import (
        extract_comment_data,
        extract_issue_metadata,
        get_issue_comments,
        get_issue_data,
    )

    issue_number = str(issue_metadata.get("number", ""))

    if not issue_number:
        st.error("No issue number found in metadata")
        return

    # Set form data in session state to match expected format
    st.session_state.form_issue_number = issue_number
    st.session_state.form_repo_info = repo

    # Fetch detailed issue data
    with st.spinner(f"Fetching issue #{issue_number} from {repo}..."):
        issue_data = get_issue_data(repo, issue_number)

        if issue_data:
            st.session_state.issue_data = issue_data
            st.session_state.issue_number = issue_number
            st.session_state.repo_info = repo

            # Extract and store issue metadata
            detailed_metadata = extract_issue_metadata(issue_data)
            st.session_state.issue_metadata = detailed_metadata
            st.session_state.issue_content = issue_data.get("body", "")

            # Fetch issue comments
            with st.spinner("Fetching issue comments..."):
                comments_data = get_issue_comments(repo, issue_number)

            if comments_data:
                st.session_state.comments_data = comments_data
                # Extract relevant comment data
                processed_comments = [extract_comment_data(comment) for comment in comments_data]
                st.session_state.processed_comments = processed_comments
            else:
                st.session_state.comments_data = []
                st.session_state.processed_comments = []
        else:
            st.error(f"Failed to fetch issue #{issue_number}")
