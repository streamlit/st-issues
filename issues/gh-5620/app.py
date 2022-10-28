import streamlit as st

if "text_key" not in st.session_state:
    st.session_state["text_key"] = "Hello, World!"

clicked = st.checkbox("Checkbox")
if clicked:
    st.text_input(label="Text input", key="text_key")
    st.write(st.session_state)
