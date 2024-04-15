import streamlit as st

class Thing(object):
    pass

st.text(f"Streamlit {st.__version__}")

options = [("Option 1", Thing()), ("Option 2", Thing())]
st.text(options[0])
st.text(options[1])

option = st.selectbox("Options:", options, format_func=lambda c: c[0])
st.text(option)
