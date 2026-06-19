"""
Reproduction for GitHub Issue #15637
Title: pressing ESC clear the contents of multiselect
URL: https://github.com/streamlit/streamlit/issues/15637

Expected: Pressing ESC should not change multiselect selections
Actual:   ESC clears all selected values from multiselect
Reported version: 1.58.0
"""
import streamlit as st

st.title("Issue #15637: ESC clears multiselect contents")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/15637)")

st.header("Issue Overview")
st.success(
    "**Expected:** Pressing ESC (to close the dropdown or a containing popover) "
    "should leave the multiselect selections untouched."
)
st.error(
    "**Actual (Bug):** Pressing ESC clears all selected values from the multiselect. "
    "This happens both when the multiselect is focused directly and when ESC is used "
    "to close a popover that contains a multiselect."
)

st.divider()

st.header("Bug Demonstration")
st.write(
    """
**Steps to reproduce:**
1. Click on the first multiselect to open its dropdown.
2. Press ESC twice — the selected options are cleared.
3. Open the popover below to see the second multiselect.
4. Press ESC to close the popover — its selected options are cleared too.
"""
)

msg = "What are your favorite colors?"
colors = ["Green", "Yellow", "Red", "Blue"]

options = st.multiselect(msg, colors, default=colors, key="1")
st.write("You selected:", options)

with st.popover("Popover"):
    options = st.multiselect(msg, colors, default=colors, key="2")
    st.write("You selected:", options)

st.divider()

st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
st.caption(
    "Reported on Streamlit 1.58.0, Python 3.14.5, Windows (multiple browsers). "
    "Reporter notes this is a regression from a previous version."
)
