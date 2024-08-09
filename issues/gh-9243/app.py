import streamlit as st

with st.popover("Foobar"):
    st.text_input("Always active")
    st.button("Active on hover")
