import streamlit as st
import pandas as pd
import numpy as np

st.write(f"Streamlit version = {st.__version__}")

df1 = pd.DataFrame(
    np.random.randn(10, 2) / [50, 50] + [37.76, -122.4],
    columns=['lat', 'lon'])

df2 = pd.DataFrame(
    np.random.randn(10, 2) / [50, 50] + [-37.76, 122.4],
    columns=['lat', 'lon'])

option = st.selectbox(
    'which dataframe to use?',
    ('1', '2'))

st.write('You selected:', option)

df = df1 if option == '1' else df2

st.map(df)
st.write(df)

st.write("df1")
st.map(df1)

st.write("2")
st.map(df2)
