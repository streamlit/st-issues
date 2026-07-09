"""Reproduction for GitHub Issue #15921
Title: Keyboard focus indicator is moving twice on the file uploader control
URL: https://github.com/streamlit/streamlit/issues/15921

Expected: File uploader has a single keyboard focus stop (the Upload button)
Actual:   Dropzone section and Upload button are both focusable — two tab stops
          for the same action
Reported version: 1.40.1
Confirmed on: 1.59.1
"""

import streamlit as st

st.title("Issue #15921: Double keyboard focus on file uploader")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/15921)")

st.header("Issue Overview")
st.write(
    "**Expected:** The file uploader should have a single keyboard-accessible focus stop — just the Upload button."
)
st.error(
    "**Actual (Bug):** Keyboard focus lands on the dropzone container first "
    "(the `<section>` wrapper), then moves to the Upload button inside it. "
    "Both elements trigger the same file-open action, creating a redundant "
    "tab stop."
)

st.divider()

st.header("Bug Demonstration")
st.write("""
**Steps:**
1. Click anywhere on this page, then press **Tab** repeatedly
2. Focus will land on the dropzone area (outline around the entire upload zone)
3. Press **Tab** again — focus moves to the **Upload** button inside the same zone
4. Both stops open the same file picker — the first is redundant
""")

st.file_uploader("Upload a file")

st.write("After the uploader, focus reaches this text input (one stop):")
st.text_input("Next focusable element")

st.divider()

st.header("Root Cause")
st.write("""
The file uploader uses [react-dropzone](https://react-dropzone.js.org/) which
assigns `tabIndex=0` to the dropzone `<section>` via `getRootProps()`. The
**Upload** button inside it is a native `<button>` (also `tabIndex=0`). Since
neither `noKeyboard` nor `tabIndex: -1` is passed to `getRootProps()`, both
elements appear in the keyboard tab order.
""")

st.divider()

st.header("Workaround")
st.write("No known workaround — this is a frontend accessibility issue.")

st.divider()

st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
