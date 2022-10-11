import streamlit as st

tab_a, tab_b, tab_c = st.tabs(["Tab-A", "Tab-B", "Tab-C"])
with tab_a:
    toggle_a = st.radio(label="toggle_a", options=["1a", "2a", "3a"], key="unique-a")
with tab_b:
    toggle_b = st.radio(label="toggle_b", options=["1b", "2b", "3b"], key="unique-b")
with tab_c:
    toggle_c = st.radio(label="toggle_c", options=["1c", "2c", "3c"], key="unique-c")