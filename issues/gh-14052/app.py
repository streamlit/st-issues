import datetime
import streamlit as st

with st.form("my_form", clear_on_submit=True):
    date_val = st.date_input(
        "Pick a date (min=2026-01-01)",
        value=datetime.date(2026, 1, 15),
        min_value=datetime.date(2026, 1, 1),
        max_value=datetime.date(2026, 12, 31),
    )
    submitted = st.form_submit_button("Submit")

if submitted:
    st.success(f"Submitted: {date_val}")
