import streamlit as st
week = st.selectbox(
    "Week",
    [1,2,3,4,5,6,7,8,9,10],
    index=8,
    key="pt_week"
)
