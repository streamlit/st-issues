import streamlit as st


def decorator(func):
    return func


with st.echo():
    @decorator
    def function():
        pass
