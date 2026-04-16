"""Reproduction app for gh-14814:
st.radio unable to select other option when using custom class instances with format_func.

Expected: Clicking "Option B" or "Option C" should select that option.
Actual: Selection snaps back to "Option A" (the default).
"""

import streamlit as st

st.title("gh-14814: st.radio custom class options")


class MyOption:
    def __init__(self, label: str, value: int):
        self.label = label
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MyOption):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)


options = [MyOption("Option A", 1), MyOption("Option B", 2), MyOption("Option C", 3)]

st.subheader("Bug: st.radio with custom class + format_func")
selected = st.radio(
    "Pick an option (bug)",
    options=options,
    format_func=lambda x: x.label,
    key="bug_radio",
)
st.write(f"Selected: {selected.label} (value={selected.value})")

st.divider()

st.subheader("Workaround: st.selectbox (works correctly)")
selected_sb = st.selectbox(
    "Pick an option (works)",
    options=options,
    format_func=lambda x: x.label,
    key="workaround_selectbox",
)
st.write(f"Selected: {selected_sb.label} (value={selected_sb.value})")
