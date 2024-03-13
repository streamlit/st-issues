import streamlit as st
import time


@st.cache_data
def cache_something():
    time.sleep(10)
    return 42


@st.cache_resource
def cache_something_else():
    time.sleep(10)
    return 42


if st.button("Run"):
    cache_something()

if st.button("Run Other"):
    cache_something_else()


st.write("foo")
