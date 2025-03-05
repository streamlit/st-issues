import streamlit as st

st.button("A")  # Has expected width.

st.button("B", help="tooltip")  # Has unexpected 100% width.
