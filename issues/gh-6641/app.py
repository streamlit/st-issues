import streamlit as st
import pandas as pd

df = pd.DataFrame({
    'A':[1,2],
    'B':[[1],[2]]
})

st.experimental_data_editor(df, num_rows='dynamic')
