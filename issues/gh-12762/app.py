"""
Reproduction for GitHub Issue #12762
Title: Component identity is ignored when using fragments and containers
Issue URL: https://github.com/streamlit/streamlit/issues/12762

Description:
When adding components to a global container from inside a fragment, a copy gets
appended instead of replacing the component, despite having set the key field.
This only happens when using fragments and containers together.

Expected Behavior:
When clicking the button repeatedly, the dataframe should be replaced (not duplicated).

Actual Behavior:
A new copy of the dataframe is appended on each button click.
"""

import pandas as pd
import streamlit as st

st.title("Issue #12762: Component Identity with Fragments & Containers")

st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/12762)")

st.header("Reproduction")

st.write("""
This app demonstrates the bug where using `st.fragment` with a global container
causes components to be duplicated instead of replaced, even when using the same `key`.
""")

# Sample data
df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})


@st.fragment
def func(container):
    show_df = st.button("Show DataFrame")
    if show_df:
        with container:
            st.dataframe(df, key="df")


container = st.container()
func(container)

st.divider()

st.header("Expected vs Actual")
st.write(
    "**Expected:** Clicking the button multiple times should replace the existing dataframe."
)
st.write(
    "**Actual:** Each click appends a new copy of the dataframe instead of replacing it."
)

st.divider()

st.header("Workaround Test")
st.write("""
The issue can be avoided by either:
1. Removing the `@st.fragment` decorator, OR
2. Not using `with container:`

Uncomment the code in the source to test these workarounds.
""")

st.divider()

st.header("Environment Info")
st.code(f"""
Streamlit version: {st.__version__}
Python version: 3.12
OS: Linux
Browser: Firefox
""")
