"""
Agent prompt dialog functionality for AI-powered issue analysis.
Contains the UI dialog for generating debugging and workaround prompts.
"""

import streamlit as st

from app.utils import display_agent_prompt, load_issue_from_metadata
from app.utils.ai.agent_prompts import generate_debugging_prompt
from app.utils.ai.agent_prompts import generate_workaround_prompt
from app.utils.github_utils import extract_issue_number


@st.dialog("🤖 Generate Agent Prompt", width="large")
def show_agent_prompt_dialog():
    """Dialog for generating agent prompts from selected issue."""
    if "selected_issue_url" not in st.session_state:
        st.error("No issue selected.")
        return

    # Extract issue number and repository
    issue_number = extract_issue_number(st.session_state.selected_issue_url)
    repo = st.session_state.get("selected_repo", "streamlit/streamlit")

    if issue_number == 0:
        st.error("Invalid issue URL.")
        return

    # Load issue data if not already loaded
    if (
        "current_agent_issue" not in st.session_state
        or st.session_state.current_agent_issue != issue_number
        or st.session_state.get("current_agent_repo") != repo
    ):
        with st.spinner(f"Loading issue #{issue_number} from {repo}..."):
            issue_metadata = {"number": issue_number}
            load_issue_from_metadata(issue_metadata, repo)
            st.session_state.current_agent_issue = issue_number
            st.session_state.current_agent_repo = repo

    # Check if issue data is loaded
    if "issue_data" not in st.session_state or "issue_metadata" not in st.session_state:
        st.error("Failed to load issue data.")
        return

    # Display issue info
    metadata = st.session_state.issue_metadata
    st.info(
        f"**{repo} Issue #{metadata.get('number')}:** {metadata.get('title', 'N/A')}"
    )

    # Prompt configuration
    col1, col2 = st.columns([2, 1])

    with col1:
        prompt_type = st.selectbox(
            "Prompt Type",
            [
                "Workaround Suggestion",
                "Debug Root Cause Analysis",
            ],
            help="""
            - **Workaround Suggestion**: Generate temporary solutions users can implement
            - **Debug Root Cause Analysis**: Deep dive into identifying the source of the problem
            """,
        )

    with col2:
        include_comments = st.checkbox("Include Comments", value=True)

    # Generate prompt button
    if st.button("🤖 Generate Agent Prompt", type="primary", width="stretch"):
        # Get issue data from session state
        issue_title = st.session_state.issue_data.get("title", "")
        issue_body = st.session_state.issue_data.get("body", "")

        comments = None
        if include_comments and "processed_comments" in st.session_state:
            comments = st.session_state.processed_comments

        # Generate the appropriate prompt based on type
        with st.spinner("Generating agent prompt..."):
            if prompt_type == "Debug Root Cause Analysis":
                prompt_data = generate_debugging_prompt(
                    issue_title=issue_title, issue_body=issue_body, comments=comments
                )
            elif prompt_type == "Workaround Suggestion":
                prompt_data = generate_workaround_prompt(
                    issue_title=issue_title, issue_body=issue_body, comments=comments
                )

        # Display the generated prompt
        display_agent_prompt(prompt_data)
