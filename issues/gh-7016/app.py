import streamlit as st
import pandas as pd

df = pd.DataFrame({'a': [1, 3], 'c': [{'s': 1, 'y': 2}, {'q': None, 'r': ''}]})
st.write(df)
