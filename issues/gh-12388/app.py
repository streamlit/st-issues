import streamlit as st

st.pills(
    "Locations",
    options=["MATCH", "Rest of the World"],
    default="MATCH",
    disabled=True,  # comment and uncomment this line
)
