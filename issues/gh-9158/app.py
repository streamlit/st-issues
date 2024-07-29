import streamlit as st


@st.fragment
def show_page():
    checkmark = st.checkbox("Yes or No")

    if checkmark:
        st.tabs(["A", "B", "C"])
    else:
        st.tabs(["1", "2"])


show_page()
