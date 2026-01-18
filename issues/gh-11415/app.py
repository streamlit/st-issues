import streamlit as st

def demo_app():
    st.title("Streamlit Bug Demo")

    # Initialize session state
    if 'persistent_choice' not in st.session_state:
        st.session_state.persistent_choice = "Option A"

    # Select box with immediate session state update
    options = ["Option A", "Option B"]
    index = 0 if st.session_state.persistent_choice == "Option A" else 1
    choice = st.selectbox("Select an option", options, index=index)

    # This line triggers the bug
    st.session_state.persistent_choice = choice

    # Variable defined in conditional branches
    result = None

    if choice == "Option A":
        st.write("Entering Option A branch")
        result = {"type": "A", "value": 100}

    if choice == "Option B":
        st.write("Entering Option B branch")
        result = {"type": "B", "value": 200}

    # This line fails with UnboundLocalError
    st.write(f"Result: {result}")

demo_app()
