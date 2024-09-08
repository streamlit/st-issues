import streamlit as st

value = st.number_input("A",min_value=1, max_value=5, key="A")

def set_too_big():
    st.session_state.A = 10

st.button("Too big", on_click=set_too_big)

st.write(value)
