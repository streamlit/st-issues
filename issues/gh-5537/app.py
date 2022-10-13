import streamlit as st

if st.button("Experimental rerun"):
    st.experimental_rerun()

if st.checkbox("Activate before rerun", key="check"):
    st.write("Text displayed before rerun")
