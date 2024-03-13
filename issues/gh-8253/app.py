import streamlit as st

list = ["30000", "40 000", "45000"]

st.data_editor(
    data = list,
    column_config = {"value": st.column_config.NumberColumn(format="%d")},
)
