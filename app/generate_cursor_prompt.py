import streamlit as st
from utils import display_cursor_prompt, display_issue_data
from utils.ai.cursor_prompts import (
    TestType,
    generate_debugging_prompt,
    generate_test_writing_prompt,
    generate_workaround_prompt,
)
from utils.github_utils import load_issue_data

# Configure page
st.set_page_config(
    page_title="Cursor Prompt Generator",
    page_icon="🤖",
)

st.title("Cursor Prompt Generator")

# Load issue data if a form submission occurred
loaded = load_issue_data()

# Display issue data if available
issue_displayed = display_issue_data()


test_type_options = [
    TestType.E2E.value,
    TestType.PYTHON_UNIT.value,
    TestType.TYPESCRIPT_UNIT.value,
]
test_type_mapping = {
    TestType.E2E.value: TestType.E2E,
    TestType.PYTHON_UNIT.value: TestType.PYTHON_UNIT,
    TestType.TYPESCRIPT_UNIT.value: TestType.TYPESCRIPT_UNIT,
}

# Create a form to generate a cursor prompt
if issue_displayed:
    st.subheader("Generate Cursor Prompt")

    # Initialize session state for prompt configuration
    if "prompt_type" not in st.session_state:
        st.session_state.prompt_type = "Write Tests Based on Bug Report"

    # Put prompt type selection outside the form so it can affect UI immediately
    st.session_state.prompt_type = st.selectbox(
        "Prompt Type",
        [
            "Workaround Suggestion",
            "Debug Root Cause Analysis",
            # TODO: Temporarily disabled until we can iterate on the prompt to give better results
            # "Write Tests Based on Bug Report",
        ],
        index=0,
    )

    # Add test type selection that only appears for test writing prompts
    test_type = TestType.UNSPECIFIED
    if st.session_state.prompt_type == "Write Tests Based on Bug Report":
        if "test_type" not in st.session_state:
            st.session_state.test_type = TestType.E2E.value

        st.session_state.test_type = st.selectbox(
            "Test Type",
            test_type_options,
            index=0,
        )
        test_type = test_type_mapping[st.session_state.test_type]

    # Use the form only for the submission and options that don't affect UI
    with st.form("cursor_prompt_form"):
        include_comments = st.checkbox("Include issue comments in prompt", value=True)
        submit_button = st.form_submit_button("Generate Cursor Prompt")

        if submit_button:
            # Get issue data from session state
            issue_title = st.session_state.issue_data.get("title", "")
            issue_body = st.session_state.issue_data.get("body", "")

            comments = None
            if include_comments and "processed_comments" in st.session_state:
                comments = st.session_state.processed_comments

            # Generate the appropriate prompt based on type
            if st.session_state.prompt_type == "Write Tests Based on Bug Report":
                prompt_data = generate_test_writing_prompt(
                    issue_title=issue_title,
                    issue_body=issue_body,
                    comments=comments,
                    test_type=test_type,
                )
            elif st.session_state.prompt_type == "Debug Root Cause Analysis":
                prompt_data = generate_debugging_prompt(
                    issue_title=issue_title, issue_body=issue_body, comments=comments
                )
            elif st.session_state.prompt_type == "Workaround Suggestion":
                prompt_data = generate_workaround_prompt(
                    issue_title=issue_title, issue_body=issue_body, comments=comments
                )

            # Store in session state so it persists after form submission
            st.session_state.cursor_prompt_data = prompt_data

    # Display the generated prompt if it exists
    if "cursor_prompt_data" in st.session_state:
        display_cursor_prompt(st.session_state.cursor_prompt_data)
