import streamlit as st

st.text_input('Input e-mail', key='test_key')

if st.button('Submit'):
    print("input: " + st.session_state['test_key'])
