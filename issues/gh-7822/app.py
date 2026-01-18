import streamlit as st

with st.form("Form"):
    st.text_input("Enter text:")
    submit = st.form_submit_button("Submit", disabled=True)

if submit:
    st.write("## 😵 Disabled form was submitted ?")
