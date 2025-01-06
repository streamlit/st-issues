import time
import streamlit as st

@st.dialog("123")
def show_dialog():
    if st.button("Close Dialog"):
        time.sleep(.15)
        st.rerun()


if st.button("Open Dialog"):
    show_dialog()
