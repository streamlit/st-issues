import streamlit as st

@st.experimental_dialog(title="Example", width="large")
def show_dialog():
    st.markdown("\n[1,2,3]\n")
    st.code("\n[1,2,3]\n")
    st.json([1, 2, 3])

if st.button("Open"):
    show_dialog()
