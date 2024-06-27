import streamlit as st

with st.form(key="some_key"):
   with st.expander("expander"):
      st.form_submit_button(label="Submit button", type="primary")
