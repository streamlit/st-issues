"""
Reproduction for GitHub Issue #13526
Title: Markdown ordered list doesn't work if it starts with a number other than 1 and is preceded by a single newline character
Issue URL: https://github.com/streamlit/streamlit/issues/13526

Description:
Demonstrates a markdown rendering bug where ordered lists starting with numbers
other than 1 don't render properly when preceded by a single newline character.

Expected Behavior:
Ordered lists should render correctly regardless of the starting number when
preceded by any number of newlines.

Actual Behavior:
Ordered lists starting with numbers other than 1 fail to render when preceded
by exactly one newline character (but work with 0 or 2+ newlines).

Reported Version: 1.52.2
"""

import streamlit as st

# === HEADER ===
st.title("Issue #13526: Markdown Ordered List Rendering Bug")

st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/13526)")

# === ISSUE OVERVIEW ===
st.header("Issue Overview")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Expected Behavior")
    st.write("""
    Ordered lists should render correctly when:
    - Starting with any number (0, 1, 10, etc.)
    - Preceded by 0, 1, or 2+ newline characters
    - Following any text content
    """)

with col2:
    st.subheader("Actual Behavior (Bug)")
    st.error("""
    Ordered lists starting with numbers **other than 1** fail to render 
    when preceded by text with **exactly 1 newline** character.
    """)

st.divider()

# === REPRODUCTION ===
st.header("🐛 Bug Demonstration")

st.write("""
The following examples show 9 different scenarios. Examples 1-7 work correctly,
but **examples 8-9 demonstrate the bug** (red thumbs down).

Each example shows the exact markdown string passed to `st.markdown()`.
""")

example = 1
for newlines, subheader in ((0, "Nothing"), (2, "Text plus 2 newlines"), (1, "Text plus 1 newline")):
    st.subheader(f"{subheader} before the ordered list")
    
    for start in (1, 0, 10):
        markdown = "\n".join(f"{i}. {s}" for i, s in enumerate(("foo", "bar"), start=start))
        if newlines:
            markdown = "Something before:" + "\n" * newlines + markdown
        
        # Determine if this example should work or is buggy
        is_buggy = newlines == 1 and start != 1
        status_icon = "🐛" if is_buggy else "✅"
        
        with st.expander(f"{status_icon} Example {example} - Start={start}, Newlines={newlines}", expanded=is_buggy):
            # Show the actual Python string being passed to st.markdown()
            st.markdown("**String passed to `st.markdown()`:**")
            st.code(repr(markdown), language="python")
            
            st.markdown("**How it renders:**")
            if is_buggy:
                st.error("❌ BUG: List doesn't render as ordered list")
            else:
                st.success("✅ Renders correctly")
            
            st.container(border=True).markdown(markdown)
        
        example += 1

st.divider()

# === DETAILED BUG EXAMPLES ===
st.header("📊 Bug Examples in Detail")

st.subheader("Example 8: Starting with 0, preceded by 1 newline (BROKEN)")

bug_example_0 = "Something before:\n0. foo\n1. bar"

st.markdown("**String passed to `st.markdown()`:**")
st.code(repr(bug_example_0), language="python")
st.error("❌ **BUG:** The list doesn't render as an ordered list.")
st.markdown("**Renders as:**")
st.container(border=True).markdown(bug_example_0)

st.divider()

st.subheader("Example 9: Starting with 10, preceded by 1 newline (BROKEN)")

bug_example_10 = "Something before:\n10. foo\n11. bar"

st.markdown("**String passed to `st.markdown()`:**")
st.code(repr(bug_example_10), language="python")
st.error("❌ **BUG:** The list doesn't render as an ordered list.")
st.markdown("**Renders as:**")
st.container(border=True).markdown(bug_example_10)

st.divider()

# === COMPARISON ===
st.header("🔍 Bug vs Workaround Comparison")

st.subheader("Broken: List starting with 10, single newline")
broken_md = "Text before:\n10. First item\n11. Second item"
st.markdown("**String passed to `st.markdown()`:**")
st.code(repr(broken_md), language="python")
st.error("❌ Renders as plain text, not as an ordered list")
st.markdown("**Renders as:**")
st.container(border=True).markdown(broken_md)

st.divider()

st.subheader("Workaround 1: Add an extra newline")
working_md_1 = "Text before:\n\n10. First item\n11. Second item"
st.markdown("**String passed to `st.markdown()`:**")
st.code(repr(working_md_1), language="python")
st.success("✅ Renders correctly with 2 newlines (notice the `\\n\\n`)")
st.markdown("**Renders as:**")
st.container(border=True).markdown(working_md_1)

st.divider()

st.subheader("Workaround 2: Start with 1 instead")
working_md_2 = "Text before:\n1. First item\n2. Second item"
st.markdown("**String passed to `st.markdown()`:**")
st.code(repr(working_md_2), language="python")
st.success("✅ Renders correctly when starting with 1")
st.markdown("**Renders as:**")
st.container(border=True).markdown(working_md_2)

st.divider()

# === WORKAROUND ===
st.header("✅ Workarounds")

st.write("""
**Option 1: Add an extra newline character**

If you need to start your list with a number other than 1, add a second newline
between the preceding text and the list.
""")

st.code("""
# Instead of:
markdown = "Text:\\n10. Item one\\n11. Item two"

# Use:
markdown = "Text:\\n\\n10. Item one\\n11. Item two"
""", language="python")

st.write("""
**Option 2: Start lists with 1**

Markdown automatically renumbers list items, so you can always start with 1
and it will display correctly regardless of newline count.
""")

st.code("""
# This always works:
markdown = "Text:\\n1. Item one\\n2. Item two"

# Markdown will renumber if you want to display different numbers
# by using HTML or other workarounds
""", language="python")

st.divider()

# === ENVIRONMENT INFO ===
st.header("Environment Info")

st.code(f"""
Streamlit version: {st.__version__}
Python version: 3.11.9
OS: MacOS
Browser: Chrome
Reported in version: 1.52.2
""")

# === TECHNICAL DETAILS ===
st.divider()

st.header("Technical Details")

st.write("""
**Affected Component:** Markdown rendering (st.markdown)

**Regression:** Yes - this used to work in a previous version

**Root Cause:** Labeled as "upstream" - issue is in the underlying markdown library

**Severity:** Medium - workaround exists but is not obvious or easily discoverable

**Related Patterns:**
- Ordered lists starting with 1 always work ✅
- Lists at the start of markdown string always work ✅
- Lists preceded by 2+ newlines always work ✅
- Lists with 1 newline + non-1 start = broken 🐛
""")

st.info("""
💡 **Note:** This is an upstream issue in the markdown rendering library used by Streamlit.
The workaround of adding a second newline character is not intuitive and many users may
not discover it, thinking it's impossible to create ordered lists starting with numbers
other than 1.
""")

