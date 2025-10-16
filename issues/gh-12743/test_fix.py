"""Test app for validating the fix for issue #12743.

This app tests that the client.showErrorDetails config option properly controls
whether deprecation warnings are shown in the browser after the fix has been applied.

Tests include:
- Manual deprecation warning trigger
- Deprecated st.cache decorator
- Deprecated query params functions

Run with different config settings to verify the fix:
  streamlit run test_fix.py --client.showErrorDetails=full
  streamlit run test_fix.py --client.showErrorDetails=stacktrace
  streamlit run test_fix.py --client.showErrorDetails=type
  streamlit run test_fix.py --client.showErrorDetails=none
"""

import streamlit as st

# Get current config value
current_config = st.config.get_option("client.showErrorDetails")

st.title("🔧 Deprecation Warning Test App")
st.header("Testing Issue #12743 Fix")

st.markdown(
    f"""
This app tests that the `client.showErrorDetails` config option properly controls
whether deprecation warnings are shown in the browser.

**Current config value:** `{current_config}`

**Expected behavior:**
- `"full"` or `True`: ✅ Deprecation warnings **SHOULD** appear in browser
- `"stacktrace"`, `"type"`, `"none"`, or `False`: ❌ Deprecation warnings **SHOULD NOT** appear in browser

Note: Deprecation warnings always log to the console regardless of config setting.
"""
)

st.divider()

st.subheader("Test 1: Trigger a Deprecation Warning")
st.markdown(
    """
Click the button below to trigger a deprecation warning. The warning will be shown
in the browser only if `showErrorDetails` is set to `"full"` or `True`.
"""
)

if st.button("Trigger Deprecation Warning"):
    # Use the deprecation util directly to show a test warning
    from streamlit.deprecation_util import show_deprecation_warning

    show_deprecation_warning(
        "🚨 **Test Deprecation Warning**\n\n"
        "This is a test deprecation warning triggered by the test app. "
        "If you see this in the browser, then `client.showErrorDetails` is set "
        'to `"full"` or `True`. If you only see this in the terminal/console, '
        'then it is set to `"stacktrace"`, `"type"`, `"none"`, or `False`.'
    )
    st.success("Deprecation warning triggered! Check above to see if it appeared.")

st.divider()

st.subheader("Test 2: Deprecated `st.cache` Decorator")
st.markdown(
    """
The `st.cache` decorator is deprecated in favor of `st.cache_data` and `st.cache_resource`.
Click the button to call a function using the deprecated decorator.
"""
)

if st.button("Use Deprecated st.cache"):
    # This will trigger a deprecation warning
    @st.cache
    def my_cached_func():
        return "Cached value"

    result = my_cached_func()
    st.success(f"Function returned: {result}")
    st.info("If deprecation warning appeared above, config is set to 'full' or True")

st.divider()

st.subheader("Test 3: Deprecated Query Params Functions")
st.markdown(
    """
`st.experimental_get_query_params` and `st.experimental_set_query_params` are deprecated.
Click to trigger the deprecation warning.
"""
)

if st.button("Use Deprecated Query Params"):
    # This will trigger a deprecation warning
    params = st.experimental_get_query_params()
    st.success(f"Query params: {params}")
    st.info("If deprecation warning appeared above, config is set to 'full' or True")

st.divider()

st.subheader("Expected Results")

expected_results = {
    "full": "✅ Deprecation warning visible in browser",
    "stacktrace": "❌ Deprecation warning NOT visible in browser (console only)",
    "type": "❌ Deprecation warning NOT visible in browser (console only)",
    "none": "❌ Deprecation warning NOT visible in browser (console only)",
    "true": "✅ Deprecation warning visible in browser (legacy)",
    "True": "✅ Deprecation warning visible in browser (legacy)",
    "false": "❌ Deprecation warning NOT visible in browser (legacy)",
    "False": "❌ Deprecation warning NOT visible in browser (legacy)",
}

# Normalize config value for lookup
config_key = str(current_config)
if config_key == "True":
    display_key = "true/True (legacy)"
    expected = expected_results.get("true", "Unknown")
elif config_key == "False":
    display_key = "false/False (legacy)"
    expected = expected_results.get("false", "Unknown")
else:
    display_key = config_key
    expected = expected_results.get(config_key, "Unknown config value")

st.markdown(
    f"""
**For your current config (`{display_key}`):**

{expected}
"""
)

st.divider()

st.subheader("How to Test Different Configs")
st.code(
    """
# Command line (recommended):
streamlit run test_fix.py --client.showErrorDetails=stacktrace

# Or create .streamlit/config.toml:
[client]
showErrorDetails = "stacktrace"

# Or set in code (requires rerun):
st.set_option("client.showErrorDetails", "stacktrace")
""",
    language="bash",
)

st.divider()

st.subheader("🐛 Issue #12743 Details")
st.markdown(
    """
**Root Cause:** The `_error_details_in_browser_enabled()` function in
`lib/streamlit/deprecation_util.py` was using `bool(config.get_option())`
which treats all non-empty strings as `True`.

**Fix:** Updated to properly check if the value equals `"full"` or is a
legacy `True` variation using the same pattern as `exception.py`.

**GitHub Issue:** https://github.com/streamlit/streamlit/issues/12743
"""
)
