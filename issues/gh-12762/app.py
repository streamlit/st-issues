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
    "**Expected:** Only ONE dataframe should be displayed, even after multiple clicks, "
    "because the same key is used (key='df'). Streamlit should recognize it's the same component."
)
st.write(
    "**Actual:** Each click creates a NEW dataframe in the container, ignoring the key. "
    "Multiple dataframes appear stacked on top of each other."
)

st.divider()

st.header("Workaround Tests")
st.write("""
The issue can be avoided by either:
1. Removing the `@st.fragment` decorator, OR
2. Not using `with container:`

Below are three comparison tests showing the different behaviors:
""")

st.subheader("Test 1: Fragment Only (No Container) ✅")
st.write("Using `@st.fragment` but NOT using `with container:`")


@st.fragment
def func_fragment_only():
    show_df = st.button("Show DataFrame (Fragment Only)", key="btn_fragment_only")
    if show_df:
        st.dataframe(df, key="df_fragment_only")


func_fragment_only()

st.divider()

st.subheader("Test 2: Container Only (No Fragment) ✅")
st.write("Using `with container:` but NOT using `@st.fragment`")


def func_container_only(container):
    show_df = st.button("Show DataFrame (Container Only)", key="btn_container_only")
    if show_df:
        with container:
            st.dataframe(df, key="df_container_only")


container2 = st.container()
func_container_only(container2)

st.divider()

st.subheader("Test 3: Neither Fragment nor Container ✅")
st.write("Regular function without `@st.fragment` or `with container:`")


def func_neither():
    show_df = st.button("Show DataFrame (Neither)", key="btn_neither")
    if show_df:
        st.dataframe(df, key="df_neither")


func_neither()

st.divider()

st.header("Environment Info")
st.code(f"""
Streamlit version: {st.__version__}
Python version: 3.12
OS: Linux
Browser: Firefox
""")
