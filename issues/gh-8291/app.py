import streamlit as st
import time

st.write(st.session_state)

st.button("button 1", key="one")

st.button("button 2", key="two")

st.button("reset")

if st.session_state.one:
    time.sleep(5)

st.write("Done running!")
