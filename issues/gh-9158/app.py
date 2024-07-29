import streamlit as st


checkmark = st.checkbox("Yes or No")

if checkmark:
    st.tabs(["A", "B", "C"])
else:
    st.tabs(["1", "2"])
