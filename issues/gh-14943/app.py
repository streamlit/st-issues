import streamlit as st

def close_first_popover():
    st.session_state.first_popover = False

def close_second_popover():
    st.session_state.second_popover = False

with st.popover("A popover", key="first_popover", on_change="rerun"):
    st.button("Close First", on_click=close_first_popover)

with st.popover("Another popover", key="second_popover", on_change="rerun"):
    st.button("Close Second", on_click=close_second_popover)
