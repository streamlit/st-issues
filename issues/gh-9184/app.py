import streamlit as st

st.slider("Slider (float step)", min_value=1.50, max_value=100.50, value=(2.5, 41.5), step=1.0)

st.slider("Slider (int step)", min_value=1.50, max_value=100.50, value=(2.5, 41.5), step=1)
