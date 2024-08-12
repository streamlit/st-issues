import streamlit as st


def decorator(*args):
    pass


with st.echo():
    @decorator
    def function():
        pass
