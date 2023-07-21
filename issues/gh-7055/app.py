import streamlit as st

@st.cache_data(experimental_allow_widgets=True, show_spinner=False)
def foo(i):
    options = ["foo", "bar", "baz", "qux"]
    st.code(options)
    r = st.radio("radio", options, index=i)
    return r

foo(1)
