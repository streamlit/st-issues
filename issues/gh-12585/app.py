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

st.header("Proper Test: Using Session State")
st.write("""
**Important:** The test above has a flaw! Because Streamlit reruns the entire script,
`ex1` and `ex2` are recreated on each run, so we're comparing against *different* objects.

Below is a proper test using `st.session_state` to persist objects across reruns:
""")

# Initialize objects in session_state (only once)
if "persisted_ex1" not in st.session_state:
    st.session_state.persisted_ex1 = Example("Persistent Hello", "World")
    st.session_state.persisted_ex2 = Example("Persistent Foo", "Bar")

st.write("**Persisted objects (created once, stored in session_state):**")
st.write(
    f"- ex1 (id: {id(st.session_state.persisted_ex1)}): {st.session_state.persisted_ex1.attr1}"
)
st.write(
    f"- ex2 (id: {id(st.session_state.persisted_ex2)}): {st.session_state.persisted_ex2.attr1}"
)

selected_persistent = st.selectbox(
    "Select Persistent Example",
    options=[st.session_state.persisted_ex1, st.session_state.persisted_ex2],
    format_func=lambda ex: ex.attr1,
    key="selectbox_persistent",
)

st.write(
    f"**Selected object (id: {id(selected_persistent)}): {selected_persistent.attr1} {selected_persistent.attr2}"
)

st.subheader("Identity Check with Persisted Objects")

col5, col6 = st.columns(2)

with col5:
    if selected_persistent is st.session_state.persisted_ex1:
        st.success("✅ Selected IS persisted_ex1")
    else:
        st.error("❌ Selected is NOT persisted_ex1")

with col6:
    if selected_persistent is st.session_state.persisted_ex2:
        st.success("✅ Selected IS persisted_ex2")
    else:
        st.error("❌ Selected is NOT persisted_ex2")

st.info(
    """
**This is the proper test!** If identity checks still fail here, then `st.selectbox`
is genuinely returning copies. If they pass, the original issue report may have been
due to misunderstanding Streamlit's execution model.
"""
)

st.divider()

st.header("Recommended Workaround: The Key Pattern ✅")
st.write("""
**Good news!** There's a clean workaround that works for all cases where object identity matters.

Instead of passing objects to selectbox, pass **keys** and look up the objects:
""")

st.subheader("Key Pattern Example")

# Store objects with keys in session_state
if "workaround_ex1" not in st.session_state:
    st.session_state.workaround_ex1 = Example("Workaround Hello", "World")
    st.session_state.workaround_ex2 = Example("Workaround Foo", "Bar")

st.write("**Objects stored in session_state:**")
st.write(
    f"- workaround_ex1 (id: {id(st.session_state.workaround_ex1)}): {st.session_state.workaround_ex1.attr1}"
)
st.write(
    f"- workaround_ex2 (id: {id(st.session_state.workaround_ex2)}): {st.session_state.workaround_ex2.attr1}"
)

# Select by KEY instead of object
selected_key = st.selectbox(
    "Select by Key",
    ["workaround_ex1", "workaround_ex2"],
    format_func=lambda key: st.session_state[key].attr1,  # Display name
    key="selectbox_workaround",
)

# Get the actual object by looking up the key
selected_by_key = st.session_state[selected_key]

st.write(
    f"**Selected object (id: {id(selected_by_key)}): {selected_by_key.attr1} {selected_by_key.attr2}"
)

st.subheader("Identity Check Results")

col7, col8 = st.columns(2)

with col7:
    if selected_by_key is st.session_state.workaround_ex1:
        st.success("✅ Selected IS workaround_ex1")
    else:
        st.error("❌ Selected is NOT workaround_ex1")

with col8:
    if selected_by_key is st.session_state.workaround_ex2:
        st.success("✅ Selected IS workaround_ex2")
    else:
        st.error("❌ Selected is NOT workaround_ex2")

st.success(
    """
**✅ This workaround works!** By selecting keys and looking up objects,
you get the actual persisted instances with preserved identity.

This pattern is always available because if object identity matters across reruns,
objects must be in session_state anyway—and session_state uses keys.
"""
)

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
