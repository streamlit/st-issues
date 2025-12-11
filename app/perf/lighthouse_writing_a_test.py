import streamlit as st

TITLE = "Lighthouse - Writing a Lighthouse Test"

st.set_page_config(page_title=TITLE)

st.header(TITLE)

DOCS = """
## Existing Tests

We already have [a few
tests](https://github.com/streamlit/streamlit/tree/develop/frontend/app/performance/apps)
that are generally not changing as they are meant to represent a consistent
high-level baseline over time. The goal is not to have a lot of these tests, but
rather a few tests that mirror a few core use cases of Streamlit, such as:

- Blank app (baseline)
- Dashboarding
- CRUD apps

These tests help ensure that Streamlit continues to perform well in these key
areas as the codebase evolves.

Generally speaking, a new Lighthouse test would only be introduced if a new core
use case is introduced to Streamlit, or if there are significant framework
changes that could impact the way the Streamlit app is perceived to be rendered
by users.
"""

st.markdown(DOCS)
