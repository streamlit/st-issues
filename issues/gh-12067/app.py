"""
Reproduction for GitHub Issue #12067
Title: st.pills incorrectly adding line breaks on the last option
Issue URL: https://github.com/streamlit/streamlit/issues/12067

Description:
When a pills widget has exactly 1 option, subsequent pills widgets incorrectly
render with a line break on the last option. This is a regression bug that
appeared in Streamlit 1.47.1.

Expected Behavior:
All pill options should render on a single line when there is space.

Actual Behavior:
The last option of pills following a 1-option pills widget wraps to a new line.

Reported Version: Streamlit 1.47.1
Root Cause: width: "auto" changed from width: "fit-content" in commit 32a82fa204
"""

import streamlit as st

# === HEADER ===
st.title("Issue #12067: Pills Line Break Regression")

st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/12067)")

# === ISSUE OVERVIEW ===
st.header("Issue Overview")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Expected Behavior")
    st.write("All pill options render on one line when there is space available.")

with col2:
    st.subheader("Actual Behavior (Bug)")
    st.error(
        "❌ Last option wraps to new line when previous pills has exactly 1 option"
    )

st.divider()

# === REPRODUCTION ===
st.header("🐛 Bug Demonstration")

st.write(
    """
**Instructions:**
1. Observe Pill 1 (has only 1 option)
2. Look at Pill 2 and Pill 3 below it
3. **BUG:** The last option ("2" for Pill 2, "3" for Pill 3) wraps to a new line
"""
)

st.error("❌ BROKEN: Single-option pills affects subsequent pills layout")

# THE BUG - This causes the line break issue
st.pills("Pill 1 (single option)", options=["1"], key="pill_1")

st.write("👇 **Notice:** Last option breaks to new line below")
st.pills("Pill 2", options=["1", "2"], key="pill_2")

st.write("👇 **Notice:** Last option breaks to new line below")
st.pills("Pill 3", options=["1", "2", "3"], key="pill_3")

st.divider()

# === COMPARISON ===
st.header("📊 Comparison: Bug vs Expected")

st.subheader("✅ Expected Behavior (No 1-option pills)")

st.write("When the first pills has 2+ options, all subsequent pills render correctly:")

st.pills("Pill 4 (TWO options)", options=["1", "2"], key="pill_4")

st.write("👇 All options on one line ✓")
st.pills("Pill 5", options=["1", "2"], key="pill_5")

st.write("👇 All options on one line ✓")
st.pills("Pill 6", options=["1", "2", "3"], key="pill_6")

st.success("✅ CORRECT: All options render on one line as expected")

st.divider()

# === ORDER TEST ===
st.header("🔬 Order Dependency Test")

st.write(
    """
**Key Finding:** The bug is order-dependent!

Moving the 1-option pills to the END (instead of beginning) also fixes it:
"""
)

st.pills("Pill 7", options=["1", "2"], key="pill_7")

st.write("👇 All options on one line ✓")
st.pills("Pill 8", options=["1", "2", "3"], key="pill_8")

st.write("👇 Single-option pills at the END doesn't cause issues")
st.pills("Pill 9 (single option at end)", options=["1"], key="pill_9")

st.success("✅ When 1-option pills comes AFTER multi-option pills, no wrapping occurs!")

st.divider()

# === WORKAROUND ===
st.header("✅ Workaround")

st.write(
    """
**Temporary workarounds until fix is deployed:**

1. **Add a dummy second option** to the first pills widget
2. **Reorder widgets** - place multi-option pills before single-option pills
3. **Use width="stretch"** - forces full width, may avoid the issue
"""
)

with st.expander("See Workaround Examples", expanded=False):
    st.subheader("Workaround 1: Add dummy option")
    st.code(
        """
# Instead of:
st.pills('Category', options=["All"], key="filter")

# Use:
st.pills('Category', options=["All", ""], key="filter")  # Add empty option
""",
        language="python",
    )

    st.subheader("Workaround 2: Reorder")
    st.code(
        """
# Move multi-option pills first:
st.pills('Options', options=["1", "2", "3"], key="options")
st.pills('Filter', options=["All"], key="filter")
""",
        language="python",
    )

st.divider()

# === ENVIRONMENT INFO ===
st.header("Environment Info")

st.code(
    f"""
Streamlit version: {st.__version__}
Python version: 3.13.5 (reported), any version affected
OS: macOS and Windows (reported)
Browser: Chrome (reported), likely affects all browsers
Regression: Yes - worked correctly before 1.47.1
"""
)

# === TECHNICAL DETAILS ===
st.divider()

st.header("Technical Details")

st.write(
    """
**Affected Components:**
- `st.pills` (ButtonGroup with PILLS style)
- `st.segmented_control` (ButtonGroup with SEGMENTED_CONTROL style)

**Regression:** Yes - worked in versions before 1.47.1

**Root Cause:**
- Commit `32a82fa204` (June 19, 2025) changed width from "fit-content" to "auto"
- Combined with maxWidth: "100%", this creates flexbox calculation errors
- 1-option pills sets narrow reference, subsequent pills miscalculate space
- Last button wraps because flex algorithm thinks there's insufficient space

**Fix:** Change width back to "fit-content" for content-width mode

**Related Issues:**
- [#12857](https://github.com/streamlit/streamlit/issues/12857) - Segmented control wrapping (different root cause, already fixed)
"""
)

with st.expander("View Code Analysis", expanded=False):
    st.code(
        """
# BEFORE (working):
const width = !containerWidth ? "fit-content" : "100%"
maxWidth: width,  # Pills had maxWidth: "fit-content"

# AFTER (broken):
const width = containerWidth ? "100%" : "auto"  # Changed!
# No maxWidth override - uses baseStyle maxWidth: "100%"
""",
        language="typescript",
    )

    st.write(
        """
**Why this causes the bug:**
- `width: "auto"` is ambiguous in flex layout
- `maxWidth: "100%"` allows container to grow incorrectly
- 1-option pills creates narrow container
- Subsequent pills inherit wrong width calculation
- Last button doesn't fit and wraps
"""
    )

st.divider()

# === SUMMARY ===
st.header("Summary")

st.write(
    """
This app demonstrates a **P2 regression bug** in Streamlit 1.47.1+ where pills
widgets with 1 option affect the layout of subsequent pills, causing their last
option to incorrectly wrap to a new line.

**What to observe:**
- Scroll up to "Bug Demonstration" section
- Pills 2 and 3 have their last options on a new line (bug)
- Pills 5, 6, 7, 8 render correctly (all options on one line)
- This proves the bug is order-dependent and related to 1-option pills
"""
)
