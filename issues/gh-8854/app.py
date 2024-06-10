import streamlit as st

import pandas as pd

st.header('Data Editor Glitch')

df = pd.DataFrame({
    'A': [1, 2, 3, 4, 5],
    'B': [10, 20, 30, 40, 50],
}).set_index('A')

st.info("""
    Let's edit the dataframe below:\n
    1. Remove the last row.\n
    2. Add a row with index (`A`) 5.""")

df_edited = st.data_editor(df, num_rows='dynamic')
st.dataframe(df_edited)
