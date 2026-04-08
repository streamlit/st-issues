"""Repro app for gh-14671: Inconsistent space encoding in query params.

Steps:
1. Select "value with spaces" from the selectbox → URL shows ?a=value%20with%20spaces
2. Click "Set query param b" → URL changes to ?a=value+with+spaces&b=value+with+spaces
   (all %20 become + when the backend overwrites the query string)
"""

import streamlit as st

st.title("gh-14671: Space encoding inconsistency")

st.selectbox(
    "Set query param `a`",
    options=("default", "value with spaces"),
    key="a",
    bind="query-params",
)

if st.button("Set query param `b`"):
    st.query_params["b"] = "value with spaces"

st.subheader("Current URL query string")
st.code(st.query_params.to_dict())
