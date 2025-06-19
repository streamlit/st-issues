import streamlit as st

with st.form("my_form"):
  st.dataframe([1, 2, 3])
  st.form_submit_button("Submit")
