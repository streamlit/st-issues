import datetime
import streamlit as st

d = st.sidebar.date_input("When's your birthday", datetime.date(2019, 7, 6))
st.write('Your birthday is:', d)
