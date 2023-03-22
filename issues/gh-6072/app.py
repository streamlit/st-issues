import datetime

import streamlit as st

st.date_input("The date is", value=(datetime.datetime.now() - datetime.timedelta(days=30), datetime.datetime.now()))
