"""
Reproduction for GitHub Issue #12743
Title: Config option client.showErrorDetails doesn't properly parse string properties for deprecation warnings
Issue URL: https://github.com/streamlit/streamlit/issues/12743

Description:
When configuring a streamlit app using client.showErrorDetails = "stacktrace" (or any
other string value), deprecation warnings are still shown in the browser even though
according to the documentation they shouldn't. Using the deprecated value false
successfully hides the warnings.

Expected Behavior:
Setting client.showErrorDetails = "stacktrace" should hide deprecation warnings in
the browser (they should only print to console).

Actual Behavior:
Deprecation warnings are still displayed in the browser when using "stacktrace".
The deprecated value false works correctly and hides warnings.

Note:
This is a regression - not reproducible in version 1.49.0, but fails in 1.50.0
"""

import plotly.graph_objects as go
import streamlit as st

st.title("Issue #12743: showErrorDetails Config String Parsing")

st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/12743)")

st.header("Configuration")

st.write("""
This app uses the config setting:
```toml
[client]
showErrorDetails = "stacktrace"
```

According to the documentation, this should hide deprecation warnings in the browser
and only show them in the console.
""")

st.divider()

st.header("Trigger Deprecation Warning")

st.write("""
The code below intentionally uses a deprecated parameter (using `width` instead of
`use_container_width` in `st.plotly_chart`) to trigger a deprecation warning.
""")

# Create a simple plotly figure
fig = go.Figure()
fig.add_trace(go.Scatter(x=[1, 2, 3, 4, 5], y=[1, 3, 2, 5, 4]))

# This will trigger a deprecation warning
st.plotly_chart(fig, width="stretch")  # Using deprecated 'width' parameter

st.divider()

st.header("Expected vs Actual")
st.write("""
**Expected:**
- With `client.showErrorDetails = "stacktrace"`, deprecation warnings should NOT
  appear in the browser (only in console)
- With `client.showErrorDetails = false` (deprecated), same behavior

**Actual:**
- With `client.showErrorDetails = "stacktrace"`, deprecation warnings ARE shown in browser ❌
- With `client.showErrorDetails = false`, deprecation warnings are correctly hidden ✅
""")

st.divider()

st.header("Technical Details")

st.write("""
The issue appears to be in the implementation at:
`lib/streamlit/deprecation_util.py` lines 30-32

The code still relies on boolean values instead of the new `ShowErrorDetailsConfigOptions` enum.
""")

st.divider()

st.header("Environment Info")
st.code(f"""
Streamlit version: {st.__version__}
Python version: 3.13.7
OS: macOS 26.0.1
Browser: Safari 26.0.1
Config: client.showErrorDetails = "stacktrace"
""")

st.divider()

st.header("Test Instructions")
st.write("""
To test this issue:
1. Look for the deprecation warning above the plotly chart
2. Check if it's displayed in the browser (BUG) or only in console (EXPECTED)
3. Try changing `.streamlit/config.toml` to use `false` instead to verify the workaround
""")
