import streamlit as st

if "new_note" not in st.session_state:
    st.session_state["new_note"] = st.container()

with st.session_state.new_note:
    title = st.session_state.new_note.text_input("Title for your note")
    if title is not None and len(title) > 0:
        content = st.session_state.new_note.text_area("Content for your note")
