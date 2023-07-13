import streamlit as st

with st.expander(label = "Test"):
     col1, col2 = st.columns(2)
     with col1:
          st.number_input("test input")
     with col2:
          st.number_input("this is my other test input")
