import streamlit as st

with st.form("form"):
    test_text = st.text_area("test", key="text area")
    test_text_2 = st.text_input("test", key="text input")
    submitted = st.form_submit_button("submit")

if submitted:
    st.write(st.session_state)
