import streamlit as st
import pandas as pd

df = pd.DataFrame({
  'first column': [1, 2, 3, 4],
  'second column': [10, 20, 30, 40],
  'third column': [10, 20, 30, 40],
  'fourth column': [10, 20, 30, 40],
  'fifth column': [10, 20, 30, 40],
  'sixth column': [10, 20, 30, 40],
  'seventh column': [10, 20, 30, 40],
  'eighth column': [10, 20, 30, 40],
  'ninth column': [10, 20, 30, 40],
  'tenth column': [10, 20, 30, 40],
})

st.write(df)
