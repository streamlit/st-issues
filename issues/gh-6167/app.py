import streamlit as st
import datetime

min_date = datetime.date(2020,1,1)
max_date = datetime.date(2020,12,31)

if 'custom_date' not in st.session_state:
  st.session_state['custom_date'] = min_date

st.date_input('Date:', min_value=min_date, max_value=max_date, value=min_date, key='custom_date')

st.write(st.session_state['custom_date'])
