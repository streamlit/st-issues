import time
import streamlit as st

with st.spinner("Running..."):
    time.sleep(2)
    st.container().columns(2)
