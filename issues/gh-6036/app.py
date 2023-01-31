import streamlit as st

with st.expander(label="https://www.google.com/"):
    st.write("No text or url shown")

with st.expander(label="[My Markdown Link]('https://www.google.com/')"):
    st.write("My Markdown Link not being displayed")

with st.expander(label="**My Markdown**"):
    st.write("Regular Bold Text shows")
