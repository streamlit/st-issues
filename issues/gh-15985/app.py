"""Reproduction for GitHub Issue #15985
Title: Typing into the selectbox doesn't search anymore after #15870
URL: https://github.com/streamlit/streamlit/issues/15985

Expected: After a value is selected, focusing the selectbox and typing clears
          the committed label and starts a fresh fuzzy search for a new option.
Actual:   Typing appends characters behind the existing selection (e.g. select
          "Banana", type "ch" -> the input shows "Bananach"), so the search
          matches nothing and the user cannot filter to a new option without
          first manually deleting the current text.
Reported version: 1.59.2 (regression since 1.59.0)

Analysis: The reporter attributes this to #15870 (selectbox dropdown
virtualization), but that PR is only in dev builds and is NOT in the stable
1.59.x releases the reporter is running. The actual regression is #15438
("Remove BaseWeb for selectbox"), the react-aria-components rewrite that first
shipped in 1.59.0. The new react-aria ComboBox keeps the committed label in the
input on focus and places the caret at the end, so the first keystroke appends
to it instead of clearing it. The old BaseWeb selectbox cleared the query on
focus/typing, which is the behavior users expect.
"""

import streamlit as st

st.title("Issue #15985: typing into selectbox doesn't search")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/15985)")

st.header("Issue Overview")
st.write(
    "**Expected:** With a value already selected, clicking the selectbox and "
    "typing clears the current label and starts a fresh search for a matching "
    "option."
)
st.error(
    "**Actual (Bug):** Typing appends behind the current selection. Select "
    "*Banana*, then type `ch` — the input becomes `Bananach` and the dropdown "
    "shows *No results* instead of filtering to *Cherry*."
)

st.divider()

st.header("Bug Demonstration")
st.write(
    """
**Steps:**
1. The selectbox below starts with **Banana** selected.
2. Click the selectbox to focus it (do **not** clear it first).
3. Type `ch` to search for *Cherry*.
4. Observe: the input reads `Bananach` and no options match, instead of
   clearing to `ch` and showing *Cherry*.
"""
)

fruits = [
    "Apple",
    "Apricot",
    "Banana",
    "Blueberry",
    "Cherry",
    "Grape",
    "Mango",
    "Orange",
    "Peach",
    "Pear",
]

value = st.selectbox("Fruit", fruits, index=2)
st.write("Selected:", value)

st.divider()

st.header("Workaround")
st.write(
    "Before typing a new query, clear the input first — e.g. select the text "
    "with `Ctrl`/`Cmd`+`A` (or triple-click) and delete it, or press "
    "`Backspace` to remove the current label. Then type to search. This is "
    "clunky and non-obvious, so it is a poor substitute for the previous "
    "type-to-search behavior."
)

st.divider()

st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
