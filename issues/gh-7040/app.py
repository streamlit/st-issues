import streamlit as st
import time

button = st.radio("How many tabs?", [5, 6])
tab_names = list(map(str, range(button)))


for tab in st.tabs(tab_names):
    with tab:
        st.header(f"you clicked button {button}")

time.sleep(5)
