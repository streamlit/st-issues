"""Issue #16003 — st.selectbox fuzzy search only matches contiguous substrings since 1.59.0.

Metadata:
  - Reporter: sfc-gh-lwilby-1
  - Introduced: 1.59.0 (react-aria ComboBox migration, PR #15438)
  - Last working: 1.58.0
  - Status: Regression confirmed; PR #16009 open with a fix
  - Versions confirmed: 1.59.0 (broken), 1.58.0 (working)
"""

import streamlit as st

st.title("Issue #16003: st.selectbox fuzzy search regression")
st.markdown(
    "**[GitHub #16003](https://github.com/streamlit/streamlit/issues/16003)** — "
    "Since 1.59.0 (react-aria ComboBox migration), `st.selectbox` fuzzy search only "
    "matches **contiguous substrings**. Non-contiguous queries that used to work "
    "now return *No results*."
)

FRUITS = ["Apple", "Apricot", "Banana", "Cherry", "Grape", "Mango", "Peach", "Pear"]

st.subheader("Reproduce")
st.markdown("Type one of the queries below into the selectbox:")

v = st.selectbox("Fruit", FRUITS, index=2)  # Banana pre-selected
st.write("Selected:", v)

col1, col2 = st.columns(2)
with col1:
    st.success(
        "**Expected behavior (1.58.0)**\n\n"
        "Fuzzy (non-contiguous) matching:\n\n"
        "| Query | Results |\n"
        "|-------|---------|\n"
        "| `ape` | Grape, Apple |\n"
        "| `aple` | Apple |\n"
        "| `rp` | Grape |"
    )
with col2:
    st.error(
        "**Actual behavior (1.59.0+)**\n\n"
        "Contiguous-substring matching only:\n\n"
        "| Query | Results |\n"
        "|-------|---------|\n"
        "| `ape` | Grape only |\n"
        "| `aple` | No results |\n"
        "| `rp` | No results |"
    )

st.subheader("Root Cause")
st.markdown(
    "React Aria's `<ComboBox>` applies its own built-in **`contains` filter** on top "
    "of Streamlit's already-fuzzy-filtered `displayOptions`. The visible list is the "
    "intersection (substring-only). Fix: pass `defaultFilter={() => true}` to "
    "`<ComboBox>` so Streamlit's own `fuzzyFilterSelectOptions` is authoritative."
)
st.markdown(
    "**Code pointer:** "
    "`frontend/lib/src/components/shared/Dropdown/Selectbox.tsx`, "
    "`<ComboBox>` component (missing `defaultFilter` prop)."
)

st.subheader("Workaround")
st.info(
    "There is no clean workaround. Users can pass `filter_mode='contains'` to get "
    "substring matching instead, but this is a different (less capable) mode and "
    "changes documented behavior. Users can also set `filter_mode='prefix'` for "
    "prefix-only matching."
)

st.subheader("Environment")
st.markdown(
    "- **Streamlit version**: 1.59.0+ (regression); 1.58.0 (last working)\n"
    "- **Python version**: 3.12\n"
    "- **Browsers**: Chromium, WebKit (both affected)\n"
    "- **OS**: Linux, macOS\n"
    "- **Introduced by**: PR #15438 (BaseWeb → react-aria ComboBox migration)"
)
