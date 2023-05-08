import streamlit as st
import pandas as pd

df = pd.DataFrame([list(range(1000))]*100)
st.dataframe(df)
