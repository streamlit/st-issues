import streamlit as st

st.number_input(
    "Test number input",
    value=None,
    help="The input cannot handle number with spaces in it.",
    key="number",
)
st.write(st.session_state["number"])
