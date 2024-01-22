import streamlit as st

placeholder = st.empty()

with placeholder.container():
  st.number_input("One", value=1)
  st.number_input("Two", value=2)

if st.button('Clear & Add'):
  placeholder.empty()
  with placeholder.container():
    st.number_input("One", value=1)
    st.number_input("Two", value=2)
    st.number_input("Three", value=3)
