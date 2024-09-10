import streamlit as st

st.slider("Select a range of values", 0.0, 100.0, (25.0, 75.0))
st.number_input("Speed (km/h)", min_value=0.1, step=0.1)
