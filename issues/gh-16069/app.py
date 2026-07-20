"""
Reproduction for GitHub Issue #16069
Title: Reduced number of supported options in selectbox while in Popover
URL: https://github.com/streamlit/streamlit/issues/16069

Expected: A selectbox with many options inside a popover opens about as fast as
          a top-level selectbox with the same options.
Actual:   Since 1.59, opening the popover is slow and gets slower the more
          options the selectbox has, because every popover open re-mounts the
          selectbox and rebuilds its full option collection.
Reported version: 1.59.2
"""

import streamlit as st

st.title("Issue #16069: selectbox in a popover is slow with many options")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/16069)")

N = 10000

# --- Issue Overview ---
st.header("Issue Overview")
st.write(
    "**Expected:** Opening the popover below is roughly as fast as opening the "
    f"top-level selectbox, even with {N:,} options."
)
st.error(
    "**Actual (Bug):** Since 1.59 the popover is noticeably slow to open, and "
    "the delay grows with the number of options. Closing and reopening the "
    "popover pays the full cost every time."
)

st.divider()

# --- Bug Demonstration ---
st.header("Bug demonstration")
st.write(
    """
**Steps:**
1. Open the popover below.
2. Click the selectbox inside it to show the options.
3. Close and reopen the popover a few times — notice the lag on each open.
4. Compare with the top-level selectbox, which opens instantly.
"""
)

st.subheader("Top-level selectbox (fast — mounted once)")
st.selectbox(label=f"Top-level, {N:,} options", options=range(N), key="bare")

st.subheader("Selectbox inside a popover (slow to open)")
with st.popover("Open popover"):
    st.selectbox(label=f"In popover, {N:,} options", options=range(N), key="popover")

st.divider()

# --- Root cause ---
st.header("Root cause")
st.write(
    """
`st.popover` unmounts its body when closed and re-mounts it on every open. The
selectbox's React Aria `ComboBox` builds its full option collection when it
mounts, so each popover open rebuilds the entire collection — an O(number of
options) cost paid on *every* open. A top-level selectbox mounts once on page
load, so it pays this cost only once.
"""
)

st.divider()

# --- Workaround ---
st.header("Workaround")
st.write(
    """
- Keep large-option selectboxes at the top level (or in a container that stays
  mounted) rather than inside a popover.
- Reduce the number of options, or use a searchable input pattern that fetches
  a smaller candidate set.
"""
)

st.divider()

# --- Environment ---
st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
