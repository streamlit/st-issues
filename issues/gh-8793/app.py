import streamlit as st
import datetime

st.subheader(f"Time: {datetime.datetime.now()}")
if st.button("🔄 Refresh UI"):
    st.rerun()
