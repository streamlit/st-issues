"""Reproduction for GitHub Issue #16281
Title: `st.status` created on a container outside a fragment corrupts the element
       tree and crashes the app with "Cannot set a node at a delta path"
URL: https://github.com/streamlit/streamlit/issues/16281

Expected: A fragment can open a status created on an outside container with two
          separate `with` statements, as it can with one created inside.
Actual:   The page goes blank and the console logs
          `Uncaught Error: Cannot set a node at a delta path`.
Reported version: 1.60.0 (regression, works on 1.58.0, broken since 1.59.0)
"""

import streamlit as st

st.title("Issue #16281: `st.status` on an outside container crashes the app")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/16281)")

st.error(
    "**Bug:** with the box below checked, the app area goes blank and the browser "
    "console logs `Uncaught Error: Cannot set a node at a delta path`. Open the "
    "developer console before checking it, then reload the page to recover."
)
st.caption("The crash is behind a checkbox because it blanks the whole page, including the issue explorer's own UI.")

if st.checkbox("Run the crashing repro"):

    @st.fragment
    def frag(outside):
        block = outside.status("query")
        with block:
            st.code("first")
        with block:  # second, separate `with` on the same status block
            st.text("second")

    frag(st.container())
