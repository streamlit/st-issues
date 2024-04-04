import streamlit as st
import time
import os

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

if st.button("Trigger Exception"):
    st.json(dict(os.environ))
    raise Exception("This is an exception")
