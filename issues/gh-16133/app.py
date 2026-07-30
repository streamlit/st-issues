"""
Reproduction for GitHub Issue #16133
Title: After entering an option with the keyboard in a multiselect, the cursor
       is positioned at the beginning of the multiselect
URL: https://github.com/streamlit/streamlit/issues/16133

Expected: After picking an option with the keyboard, the text cursor stays at
          the end of the input, so the next typed characters appear where you
          expect them.
Actual:   After clearing the selection (Escape) and re-selecting an option, the
          cursor jumps to the beginning of the multiselect input, so newly typed
          text is inserted before the placeholder/existing content.
Reported version: 1.60.0
"""

import streamlit as st

st.title("Issue #16133: multiselect cursor jumps to start after keyboard select")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/16133)")

# --- Issue Overview ---
st.header("Issue Overview")
st.write(
    "**Expected:** After selecting an option with the keyboard, the text cursor "
    "remains at the end of the input so the next characters you type land where "
    "you expect."
)
st.error(
    "**Actual (Bug):** After the first keyboard selection the cursor sits after "
    "the chosen item, but once you clear the selection and re-select, the cursor "
    "jumps to the *beginning* of the input, making further typing hard to follow."
)

st.divider()

# --- Bug Demonstration ---
st.header("Bug demonstration")
st.write(
    """
**Steps (keyboard only, no mouse after the first click):**
1. Click the multiselect below to focus it.
2. Type `Red` and press **Enter** — "Red" is selected.
3. Press **Escape** twice to close the dropdown and clear the selection.
4. Type `Red` again and press **Enter**.
5. Start typing another query — observe the caret is at the **start** of the
   input instead of after your text.

Reported in Edge, Opera, and Firefox. This is a regression — earlier versions
kept the caret at the end.
"""
)

options = st.multiselect(
    "What are your favorite colors?",
    ["Green", "Yellow", "Red", "Blue"],
    default=[],
)
st.write("You selected:", options)

st.divider()

# --- Environment ---
st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
st.code(
    "Reported on: Streamlit 1.60.0\n"
    "Browsers: Edge, Opera, Firefox\n"
    "Regression: yes (worked in previous versions)"
)
