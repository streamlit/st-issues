import streamlit as st
from datetime import datetime

get_type = lambda: "primary" if "st_reset_type" in st.session_state and st.session_state.st_reset_type else "secondary"
if reset := st.button(
    key="st_reset_type",
    label="Reset",
    type=get_type()
    ):
    st.write(f"click time: {datetime.now()}")
st.write(f"button: {reset}")
