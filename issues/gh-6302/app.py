import streamlit as st

block = """
    line 1
    line 2
    line 3
"""

st.code(block)
st.markdown(f"```\n{block}\n```")
