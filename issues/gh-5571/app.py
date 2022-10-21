import streamlit as st
from datetime import date, timedelta

today = date.today()
today_minus_30 = today - timedelta(days=30)

# Date input - doesn't work
st.session_state.my_date_input = (today_minus_30, today)
st.date_input(
    label="Date input",
    max_value=today,
    key="my_date_input"
)

# Date input - works
st.date_input(
    label="Date input 2",
    max_value=today,
    value=(today_minus_30, today),
    key="my_date_input_2"
)
