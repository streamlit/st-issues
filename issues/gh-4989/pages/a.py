import streamlit as st

st.write('st.session_state', st.session_state)
st.text_input('inp', key='shared_input')