import streamlit as st

text = """
  Here is some code:
  
  ```
  import streamlit as st
  st.write("Hello world!")
  # this is a very long comment just to demonstrate the overflowing behavior it goes on and on and on
  ```
"""
st.code(text, language="python")

e = StreamlitAPIException()
st.exception(e)
