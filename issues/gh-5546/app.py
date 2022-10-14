import streamlit as st

values = [1_000_000 + x for x in range(1000)]
st.select_slider('Select a value', values, value=values[0])
