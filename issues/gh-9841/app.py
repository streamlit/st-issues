import streamlit as st

with st.form("form"):
    test_text = st.text_area("test", key="test input")
    submitted = st.form_submit_button("submit")

if submitted:
    st.write(st.session_state)
