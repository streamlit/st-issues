import streamlit as st


checkmark = st.checkbox("Yes or No - Outside Fragment")

if checkmark:
    st.tabs(["A", "B", "C"])
else:
    st.tabs(["1", "2"])


checkmark = st.checkbox("Yes or No - Inside Fragment")

if checkmark:
    st.tabs(["A", "B", "C"])
else:
    st.tabs(["1", "2"])
