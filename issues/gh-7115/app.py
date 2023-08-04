import streamlit as st
import time


st.set_page_config(layout="wide")
st.toast("welcome to chat 1.\n\nthis is second line.\n\nthis is third line.")
prompt = st.chat_input("input here")
time.sleep(1)
st.toast("welcome to chat 2.\n\nthis is second line.\n\nthis is third line.")
