"""
Reproduction for GitHub Issue #12585
Title: Selectboxes return copies and not actual selection
Issue URL: https://github.com/streamlit/streamlit/issues/12585

Description:
st.selectbox returns a copy of the selected object rather than the actual object
from the options list. This breaks identity checks (using 'is' operator) and can
be problematic when working with singletons or when object identity matters.

Expected Behavior:
st.selectbox should return the exact same object instance that was provided in
the options list.

Actual Behavior:
st.selectbox returns a copy of the selected object, which fails identity checks
even though the values are equal.

Note: This issue was originally reported in 2021 (#3703) but hasn't been resolved.
"""

import streamlit as st


class Example:
    attr1: str
    attr2: str

    def __init__(self, attr1: str, attr2: str) -> None:
        self.attr1 = attr1
        self.attr2 = attr2


st.title("Issue #12585: Selectbox Returns Copies Not Actual Objects")

st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/12585)")

st.header("Reproduction")

st.write("""
This app demonstrates that `st.selectbox` returns a copy of the selected object
rather than the actual object from the options list.
""")

# Create example objects
ex1 = Example("Hello", "World")
ex2 = Example("Foo", "Bar")
ex_list = [ex1, ex2]

st.write("**Created objects:**")
st.write(f"- ex1 (id: {id(ex1)}): {ex1.attr1} {ex1.attr2}")
st.write(f"- ex2 (id: {id(ex2)}): {ex2.attr2} {ex2.attr2}")

st.divider()

selected = st.selectbox("Example", options=ex_list, format_func=lambda ex: ex.attr1)

st.write(f"**Selected object (id: {id(selected)}): {selected.attr1} {selected.attr2}")

st.divider()

st.header("Identity Check Results")

# Test identity with 'is' operator
col1, col2 = st.columns(2)

with col1:
    if selected is ex1:
        st.success("✅ Selected is ex1")
    else:
        st.error("❌ Selected is NOT ex1")

with col2:
    if selected is ex2:
        st.success("✅ Selected is ex2")
    else:
        st.error("❌ Selected is NOT ex2")

st.divider()

st.header("Equality Check Results")

st.write("**Checking equality (==) instead of identity (is):**")

col3, col4 = st.columns(2)

with col3:
    # Note: This will fail because Example class doesn't implement __eq__
    st.write(f"selected == ex1: {selected == ex1}")

with col4:
    st.write(f"selected == ex2: {selected == ex2}")

st.divider()

st.header("Expected vs Actual")
st.write("""
**Expected:**
- The `selected` object should be identical to one of the original objects (ex1 or ex2)
- Identity check with `is` operator should return `True`
- Memory addresses should match

**Actual:**
- The `selected` object is a copy with a different memory address
- Identity check with `is` operator returns `False`
- This breaks patterns that rely on object identity (singletons, caching, etc.)
""")

st.divider()

st.header("Impact")
st.write("""
This issue is problematic when:
- Working with singleton patterns
- Using object identity for comparisons
- Managing object caching or memoization
- Tracking specific instances across the application
""")

st.divider()

st.header("Environment Info")
st.code(f"""
Streamlit version: {st.__version__}
Python version: 3.10
OS: MacOS
Browser: Chrome
""")

st.divider()

st.header("Additional Context")
st.write("""
This issue was originally reported in 2021 as issue #3703 but moved to enhancement
without resolution. It remains a significant limitation when working with objects
where identity matters.
""")

