"""Issue #16004 — st.selectbox Escape no longer clears the typed search query since 1.59.0.

Metadata:
  - Reporter: sfc-gh-lwilby-1
  - Introduced: 1.59.0 (BaseWeb -> react-aria ComboBox migration, PR #15438)
  - Last working: 1.58.0
  - Status: Regression confirmed via Playwright (1.59.0 broken, 1.58.0 works)
  - Versions confirmed: 1.59.0 (broken), 1.58.0 (working)
"""

import streamlit as st

st.title("Issue #16004: st.selectbox Escape does not clear the typed query")
st.markdown(
    "**[GitHub #16004](https://github.com/streamlit/streamlit/issues/16004)** — "
    "Since 1.59.0 (react-aria ComboBox migration), pressing **Escape** while "
    "searching a value-selected `st.selectbox` no longer discards the typed query. "
    "The dropdown closes and the committed value is preserved, but the half-typed "
    "query stays visible in the input."
)

FRUITS = ["Apple", "Apricot", "Banana", "Cherry", "Grape", "Mango", "Peach", "Pear"]

st.subheader("Reproduce")
st.markdown(
    "1. The selectbox below has **Banana** committed.\n"
    "2. Click it and type `gr` (do **not** pick an option).\n"
    "3. Press **Escape**.\n"
    "4. Look at the input vs. the committed value below."
)

v = st.selectbox("Fruit", FRUITS, index=2)  # Banana pre-selected
st.write("Committed value:", v)

col1, col2 = st.columns(2)
with col1:
    st.success(
        "**Expected (1.58.0)**\n\n"
        "Escape discards the query and restores the committed label:\n\n"
        "- Input shows `Banana` again\n"
        "- `value` stays `Banana`"
    )
with col2:
    st.error(
        "**Actual (1.59.0+)**\n\n"
        "Escape closes the dropdown but keeps the stale query:\n\n"
        "- Input shows `gr` (the half-typed query)\n"
        "- `value` is still `Banana` (no wrong commit)\n"
        "- Typing again appends to the stale query"
    )

st.info(
    "**Control:** repeat the steps but click elsewhere (blur) instead of pressing "
    "Escape — the input correctly restores `Banana`. Only the **Escape** path is "
    "affected."
)

st.subheader("Root Cause")
st.markdown(
    "In `frontend/lib/src/components/shared/Dropdown/Selectbox.tsx`, "
    "`handleInputKeyDownCapture` handles Escape **only** for *clearable* "
    "selectboxes (it commits `null`). For a non-clearable selectbox (the default), "
    "Escape falls through to react-aria's `<ComboBox>`, which closes the dropdown "
    "but never resets the **controlled** `inputValue`. The blur path "
    "(`handleBlur`) already restores `inputValue` to the committed label — Escape "
    "has no equivalent, so the stale query survives.\n\n"
    "**Fix direction:** add an Escape branch for the non-clearable case that "
    "mirrors `handleBlur` — reset `inputValue` to the committed label, clear the "
    "active-filter state, and close the dropdown."
)

st.subheader("Workaround")
st.info(
    "Instead of Escape, **click elsewhere** (blur) to dismiss the search — this "
    "restores the committed value. Re-focusing and retyping also works, though the "
    "stale query must be cleared first."
)

st.subheader("Environment")
st.markdown(
    "- **Streamlit version**: 1.59.0+ (regression); 1.58.0 (last working)\n"
    "- **Python version**: 3.12\n"
    "- **Browsers**: Chromium, WebKit (both affected)\n"
    "- **OS**: browser-independent\n"
    "- **Introduced by**: PR #15438 (BaseWeb -> react-aria ComboBox migration)\n\n"
    f"Running on Streamlit `{st.__version__}`."
)
