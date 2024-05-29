import streamlit as st
import time
import os

if "foo" not in st.session_state:
    st.session_state["foo"] = "bar"
    st.rerun()

st.write("works")
