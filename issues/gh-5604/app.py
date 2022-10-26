import streamlit as st
from time import sleep

if "texttt" not in st.session_state:
    st.session_state["texttt"] = "Hello, World!"

if st.button("Press before expanding"):
    with st.spinner():
        sleep(1)

with st.expander("Text Field inside"):
    st.text_area("Text", key="texttt")
    st.write(st.session_state)
