import streamlit as st

st.title("App")

tab1, tab2 = st.tabs(["Tab1", "Tab2"])
tab1.write("This is tab 1")
l = ["foo", "bar", "baz"] * 30
tab2.table(l)
