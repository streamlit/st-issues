import streamlit as st

@st.dialog("Test")
def test():
    st.dataframe({"a": [2,3], "b": [3,4]})

test()
