import streamlit as st

class test_class:
    def __init__(self, text, value):
        self.text = text
        self.valu = value

elements = [
    test_class("A", 1),
    test_class("B", 2)
]
st.multiselect("Test", elements, format_func=lambda x: x.text)
