"""Reproduction for GitHub Issue #14672
Title: Possible Regression: Conditional Block Type Change (whitescreen when switching between expander and tabs)
Issue URL: https://github.com/streamlit/streamlit/issues/14672

Description:
When conditionally switching between different block types (st.expander and st.tabs),
the app may display a blank white screen instead of rendering the selected block.

Expected Behavior:
Toggling the checkbox should smoothly switch between expander and tabs without any visual issues.

Actual Behavior:
The app shows a blank white screen when toggling the checkbox. No errors in console.

Reported Version: 1.56.0
Reported Browser: Firefox 149.0 (aarch64)
"""

import time

import streamlit as st

st.title("Issue #14672: Whitescreen switching expander ↔ tabs")

st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/14672)")

st.header("Issue Overview")

st.write("**Expected:** Toggling the checkbox smoothly switches between an expander and tabs.")
st.error("**Actual (Bug):** The app may show a blank white screen when toggling. Reported on Firefox 149.0.")

st.divider()

st.header("🐛 Bug Demonstration")

st.write("""
Instructions for testing:
1. Click the "Click me!" checkbox below to uncheck it
2. Observe whether tabs appear or the screen goes blank
3. Click again to toggle back to the expander
4. Repeat a few times to check for intermittent behavior
""")

st.warning("⚠️ This bug was reported on **Firefox 149.0**. If you cannot reproduce on Chrome, please try Firefox.")

if st.checkbox("Click me!", True):
    with st.expander("Something", expanded=True):
        st.write("Do something 1")
        st.write("Do something 2")
        st.write("Do something 3")
        st.write("Do something 4")
        st.write("Do something 5")
        st.write("Do something 6")
else:
    tab1, tab2, tab3 = st.tabs(["1", "2", "3"])
    with tab1:
        st.info("Some info in tab1.")
    with tab2:
        st.info("Some info in tab2.")
    with tab3:
        st.info("Some info in tab3.")

time.sleep(1)

st.divider()

st.header("📊 Additional Test Cases")

st.subheader("Tabs → Expander (reverse direction)")

if st.checkbox("Show tabs (uncheck for expander)", True, key="reverse"):
    tab1, tab2 = st.tabs(["A", "B"])
    with tab1:
        st.write("Tab A content")
    with tab2:
        st.write("Tab B content")
else:
    with st.expander("Expander", expanded=True):
        st.write("Expander content")

st.divider()

st.subheader("Tabs → Container")

if st.checkbox("Show tabs (uncheck for container)", True, key="container"):
    tab1, tab2 = st.tabs(["X", "Y"])
    with tab1:
        st.write("Tab X content")
    with tab2:
        st.write("Tab Y content")
else:
    with st.container(border=True):
        st.write("Container content")

st.divider()

st.header("Environment Info")

st.code(f"""
Streamlit version: {st.__version__}
Reporter's version: 1.56.0
Reporter's browser: Firefox 149.0 (aarch64)
Reporter's OS: macOS 15.7.3 (24G419)
""")

st.header("Technical Details")

st.write("""
**Affected Component:** Block rendering / block type reconciliation

**Regression:** Reportedly fixed in PR #9276, which changed `AppRoot.addBlock` to not
preserve children when a block's type changes at the same delta path. The fix is still
present in the codebase — this may be a different manifestation.

**Related Issues:** #9276, #9259, #8676

**Investigation Notes:**
- Could not reproduce on Chromium or WebKit (Playwright) on 1.56.0
- Firefox-specific rendering or timing may be involved
- The `time.sleep(1)` in the repro may create timing conditions
- The tab container block does not set `allow_empty = True`, which could cause a
  brief blank render during block type transitions
""")
