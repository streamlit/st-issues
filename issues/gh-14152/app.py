import streamlit as st

st.text_input("Test Main")

with st._bottom:
  st.text_input("Test Bottom")
