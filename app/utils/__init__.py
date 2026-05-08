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
