import streamlit as st
import pandas as pd


df = pd.DataFrame({
    'col1': [1,2],
    'col2': ['asdf,jklh','qwerrtyu']
})

st.dataframe(df)
