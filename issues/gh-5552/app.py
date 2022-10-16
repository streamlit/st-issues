import streamlit as st

tab_names = []
for i in range(100):
  tab_names.append(str(i)*4)

tabs = st.tabs(tab_names)
