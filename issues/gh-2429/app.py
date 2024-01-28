import streamlit as st
import datetime

start_date, end_date = st.date_input(label='Test', value=(datetime.date(2019,7,6), datetime.date(2020, 7 ,6)))
st.write(start_date)
st.write(end_date)
