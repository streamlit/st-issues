import streamlit as st
from datetime import datetime

start_time = st.time_input("Time from:")

search_jobs_btn = st.button("Click")
current_time = datetime.now().strftime("%H:%M:%S")
st.write(f"Current time: {current_time}. Time input: {start_time}")
