import streamlit as st

if st.session_state.get("apply_workaround"):
    for key in st.session_state:
        st.session_state[key] = st.session_state[key]

st.write('st.session_state', st.session_state)
st.text_input('inp', key='shared_input')
