import streamlit as st

# Some long code sample
CODE = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.\n"
    * 1373
)

# Displaying this will cause issues
st.code(CODE, language="sql")


@st.dialog("dialogue")
def show_dialogue():
    st.write("This is a dialogue")


with st.sidebar:
    # This won't open on subsequent presses
    if st.button("Show Dialogue"):
        show_dialogue()
