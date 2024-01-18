import streamlit as st
import pandas as pd

init_df = pd.DataFrame({'name': ["1", "2"], 'Dict': [{"1": 1, "2": 2}, {"3": 3, "4": 4}]})

st.write(init_df["Dict"][0]["1"])  # outputs 1

df = st.data_editor(init_df, disabled="Dict")

st.write(df["Dict"][0]["1"])  # "TypeError: string indices must be integers, not 'str'"
