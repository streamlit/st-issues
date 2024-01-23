import streamlit as st
import pandas as pd

d = {"lat": [40.781243], "lon": [-73.968432]}

df = pd.DataFrame.from_dict(d)

with st.expander("map"):
    st.map(df, size=2)

if st.checkbox("Add extra map"):
    st.map(df, size=2)
