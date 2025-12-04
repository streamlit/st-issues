import streamlit as st

def a():
    st.header("Header A")

def b():
    st.header("Header B")

st.sidebar.header("Sidebar Header")
st.navigation((a, b), position="top").run()
