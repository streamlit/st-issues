import streamlit as st

tabs = st.tabs(["Tab 1", "Tab 2", "Tab 3"])

for tab in tabs:
    tab.html("<h1>Hello</h1><p>This is a test</p>")
