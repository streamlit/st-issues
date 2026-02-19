import streamlit as st

st.title("Widget flicker issue")
st.write(st.__version__)

with st.spinner("Starting up..."):
    # In this minimal example, do nothing here.
    # In a real app, one might import any large packages within this spinner context.
    pass

foo, bar = st.tabs(["tab_one", "tab_two"])
with bar:
    st.number_input("number")
