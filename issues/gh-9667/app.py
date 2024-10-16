import streamlit as st
import datetime

test_date = st.sidebar.date_input('Test date', None, datetime.date(2016, 6, 28), datetime.date(2018, 4, 13))
