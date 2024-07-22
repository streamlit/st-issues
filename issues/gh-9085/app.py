import streamlit as st

options = []

for i in range(100):
    options.append(("foo " * (i + 1)) + f"{i}")

st.multiselect("My multiselect", options, options)
