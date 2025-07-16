import streamlit as st
from github.issues import (
    extract_comment_data,
    extract_issue_metadata,
    get_issue_comments,
    get_issue_data,
)


def load_issue_data():
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
    # Check for GitHub token
    token = st.secrets.get("GH_TOKEN")
    if not token:
        st.error("⚠️ No GH_TOKEN secret found. Please add a secret to your app.")
        return False

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
            token,
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
                    token,
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
