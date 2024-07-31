import time
import streamlit as st

time.sleep(0.1)  # simulates calculation

with st.popover('Popover'):
    if st.button('Button'):
        st.rerun()
