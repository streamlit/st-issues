import streamlit as st

@st.fragment(run_every="2s")
def live_tasks_table():
    st.write("hello")

live_tasks_table()
