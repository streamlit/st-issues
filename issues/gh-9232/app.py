import streamlit as st

print("before")
if st.button("Refresh"):
    st.rerun()
    print("after")
