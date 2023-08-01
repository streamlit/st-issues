import streamlit as st
from datetime import date

st.date_input('date', value=(date(2023,1,1),date(2023,1,2)))
