import streamlit as st

class foo():
    def __init__(self, a):
        self.a = a
    def __repr__(self):
        return "foo " + self.a
    def __str__(self):
        return self.a

options = [foo("a"),"a"]

c = st.multiselect("C", options=options)
c

b = st.multiselect("D", options=["A", "B", "B", "C", "C", "C"])
b
