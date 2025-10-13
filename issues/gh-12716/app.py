"""
Reproduction for GitHub Issue #12716
Title: Long dialog starts at the bottom
Issue URL: https://github.com/streamlit/streamlit/issues/12716

Description:
When a dialog has enough content to require a scrollbar, it starts scrolled to the
bottom instead of the top. Users must scroll up to see the first entries.

Expected Behavior:
Dialog should start at the top, showing the first content.

Actual Behavior:
Dialog starts scrolled to the bottom, showing the last content.
"""

import streamlit as st

st.title("Issue #12716: Long Dialog Starts at Bottom")

st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/12716)")

st.header("Reproduction")

st.write("""
Click the button below to open a long dialog. The dialog contains numbered sections
from 1 to 20. 

**Expected:** You should see "Section 1" at the top when the dialog opens.

**Actual (Bug):** The dialog starts scrolled to the bottom, showing "Section 20" first.
You have to scroll UP to see the earlier sections.
""")


@st.dialog("Long Dialog Example")
def show_long_dialog():
    st.error(
        "⬆️ **THIS IS THE TOP** - If you see this first, the dialog is working correctly!"
    )

    st.write("This dialog has 20 sections to make it long enough to require scrolling.")

    st.divider()

    # Generate lots of content to make the dialog scrollable
    for i in range(1, 21):
        st.subheader(f"Section {i}")
        st.write(
            f"""
        This is section {i} of the dialog. In a properly functioning dialog,
        you should see Section 1 first when the dialog opens, not Section 20.
        """
        )
        if i < 20:
            st.divider()

    st.divider()

    st.success(
        "⬇️ **THIS IS THE BOTTOM** - If you see this first when opening the dialog, that's the bug!"
    )

    if st.button("Close", key="close_dialog"):
        st.rerun()


if st.button("Open Long Dialog", type="primary"):
    show_long_dialog()

st.divider()

st.header("Expected vs Actual")

st.write("""
**Expected:**
- When dialog opens, you should see the top of the content first
- "THIS IS THE TOP" message and "Section 1" should be visible
- User can scroll DOWN to see more content

**Actual (Bug):**
- Dialog opens scrolled to the bottom
- "THIS IS THE BOTTOM" message and "Section 20" are visible first
- User must scroll UP to see the beginning
""")

st.divider()

st.header("Impact")

st.write("""
This is particularly problematic for:
- Forms in dialogs (users miss the first fields)
- Instructions at the top of dialogs
- Any dialog where reading order matters
- Long help text or documentation in dialogs
""")

st.divider()

st.header("Environment Info")
st.code(
    f"""
Streamlit version: {st.__version__}
Python version: (reported with no specific version)
Operating System: (not specified)
Browser: (not specified)
"""
)

