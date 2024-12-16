import time
import streamlit as st
@st.cache_data
def show_data():
    with st.status("Downloading data...", expanded=True) as status:
        st.write("Searching for data...")
        time.sleep(2)
        st.write("Found URL.")
        time.sleep(1)
        st.write("Downloading data...")
        time.sleep(1)
        status.update(
            label="Download complete!", state="complete", expanded=False
        )

show_data()
