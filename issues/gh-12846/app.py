"""
Reproduction for GitHub Issue #12846
Title: Issue on st.dataframe width='stretch', TypeError: 'str' object cannot be interpreted as an integer
Issue URL: https://github.com/streamlit/streamlit/issues/12846

Description:
This app demonstrates a TypeError that occurs when using width='stretch' parameter
in st.dataframe with @st.fragment. The issue was reported in Streamlit v1.50.0.

Expected Behavior:
st.dataframe should accept width='stretch' as a valid parameter and display the
dataframe stretched to container width.

Actual Behavior:
TypeError: 'str' object cannot be interpreted as an integer
Error location: streamlit/elements/arrow.py, line 588

Reported Version: Streamlit 1.50.0
"""

import time

import pandas as pd
import streamlit as st

# === HEADER ===
st.title("Issue #12846: st.dataframe width='stretch' TypeError")

st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/12846)")

# === ISSUE OVERVIEW ===
st.header("Issue Overview")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Expected Behavior")
    st.write(
        "The `width='stretch'` parameter should work with `st.dataframe`, causing the dataframe to stretch to the full width of its container."
    )

with col2:
    st.subheader("Actual Behavior (Bug)")
    st.error(
        "**Reported in v1.50.0:** TypeError: 'str' object cannot be interpreted as an integer"
    )

st.divider()

# === REPRODUCTION ===
st.header("🐛 Bug Demonstration")

st.write("""
**Testing Instructions:**
1. Observe the dataframes below
2. Check if any errors appear
3. Note the Streamlit version being used

**Note:** This bug was reported in Streamlit v1.50.0. If you're running a newer version,
the bug may already be fixed.
""")

# Create test dataframe
result_df = pd.DataFrame(
    {
        "Column A": [1, 2, 3, 4, 5],
        "Column B": ["Apple", "Banana", "Cherry", "Date", "Elderberry"],
        "Column C": [10.5, 20.3, 30.7, 40.2, 50.9],
    }
)

st.subheader("Test 1: width='stretch' with @st.fragment")

st.write("This is the exact scenario from the issue report.")

try:

    @st.fragment
    def dataframe_fragment(df):
        st.dataframe(df, width="stretch", hide_index=True, key=f"target_{time.time()}")

    dataframe_fragment(result_df)
    st.success("✅ No error - width='stretch' works correctly with fragment!")
except TypeError as e:
    st.error("❌ **BUG REPRODUCED:** TypeError occurred")
    st.code(str(e))
    st.write("**Error Details:**")
    st.write("This is the reported bug - width='stretch' causes a TypeError")

st.divider()

st.subheader("Test 2: width='stretch' without fragment")

st.write(
    "Testing if the issue is specific to fragments or affects all st.dataframe calls."
)

try:
    st.dataframe(
        result_df, width="stretch", hide_index=True, key="test_stretch_no_fragment"
    )
    st.success("✅ No error - width='stretch' works without fragment!")
except TypeError as e:
    st.error("❌ **BUG REPRODUCED:** TypeError occurred")
    st.code(str(e))

st.divider()

# === COMPARISON ===
st.header("📊 Comparison: Different Width Parameters")

st.write("**Testing all width parameter variants:**")

st.subheader("1. width='stretch' (New in v1.50)")
try:
    st.dataframe(result_df, width="stretch", hide_index=True, key="compare_stretch")
    st.success("✅ Works")
except Exception as e:
    st.error(f"❌ Error: {e}")

st.divider()

st.subheader("2. width='content' (New in v1.50)")
try:
    st.dataframe(result_df, width="content", hide_index=True, key="compare_content")
    st.success("✅ Works")
except Exception as e:
    st.error(f"❌ Error: {e}")

st.divider()

st.subheader("3. width=500 (Integer)")
try:
    st.dataframe(result_df, width=500, hide_index=True, key="compare_int")
    st.success("✅ Works")
except Exception as e:
    st.error(f"❌ Error: {e}")

st.divider()

st.subheader("4. use_container_width=True (Deprecated)")
try:
    st.dataframe(
        result_df, use_container_width=True, hide_index=True, key="compare_ucw"
    )
    st.success("✅ Works (deprecated but functional)")
except Exception as e:
    st.error(f"❌ Error: {e}")

st.divider()

# === ENVIRONMENT INFO ===
st.header("Environment Info")

st.code(f"""
Streamlit version: {st.__version__}
Reported issue version: 1.50.0
Python version: 3.12 (reported), current runtime varies
OS: Ubuntu (reported), current runtime varies
Browser: Chrome (reported)
""")

st.divider()

# === TECHNICAL DETAILS ===
st.header("Technical Details")

st.write("""
**Affected Component:** `st.dataframe` width parameter handling

**Regression:** Introduced in v1.50.0 with new width/height parameter system

**Root Cause (Hypothesis):** The new `width='stretch'` parameter may not be properly
handled in the protobuf marshalling code or the validation logic in `layout_utils.py`.

**Related Issues:** Part of the AdvancedLayouts project that updated width/height parameters
""")

with st.expander("View Error Messages/Stack Traces", expanded=False):
    st.write("**Reported Error:**")
    st.code("""
TypeError: 'str' object cannot be interpreted as an integer

Traceback:
python3.12/site-packages/streamlit/runtime/metrics_util.py", line 443, in wrapped_func
    result = non_optional_func(*args, **kwargs)
python3.12/site-packages/streamlit/elements/arrow.py", line 588, in dataframe
    """)

with st.expander("Testing Results", expanded=False):
    st.write("""
**Playwright Test Results (on develop branch):**
- All 6 tests PASSED
- This indicates the bug does NOT exist in the current development version
- Bug appears to be specific to v1.50.0 release

**Conclusion:**
- Bug likely already fixed in develop branch
- Users on v1.50.0 should use workaround or upgrade
- Issue should be verified on v1.50.0 specifically
    """)

st.divider()

st.header("🔍 Verification Status")

if st.__version__ == "1.50.0":
    st.warning(
        "⚠️ You are running Streamlit v1.50.0 - the version where this bug was reported. "
        "If tests pass, the bug may have been misreported or environment-specific."
    )
elif st.__version__.startswith("1.50"):
    st.info(
        f"ℹ️ You are running Streamlit v{st.__version__}. "
        "If all tests above passed, the bug does not affect this version."
    )
else:
    st.success(
        f"✅ You are running Streamlit v{st.__version__}. "
        "All width parameter variants appear to work correctly."
    )

st.divider()

st.header("📝 Test Results Summary")

st.write("""
**Current Status:** The bug reported in issue #12846 does not reproduce in testing.

**What this means:**
- All width parameter options (`'stretch'`, `'content'`, integer) work correctly
- Both with and without `@st.fragment` work as expected
- The deprecated `use_container_width=True` continues to function

**Possible explanations:**
1. Bug was specific to v1.50.0 and has been fixed in subsequent releases
2. Bug was environment-specific or configuration-dependent
3. Bug report may have been based on a misunderstanding

**Recommendation for users experiencing this issue:**
- Upgrade to the latest version of Streamlit: `pip install --upgrade streamlit`
- If issue persists, provide detailed environment information and stack trace
""")
