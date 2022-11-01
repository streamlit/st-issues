import pandas as pd
import streamlit as st

df = pd.DataFrame([[{‘1’:‘2’}, ‘abc’], [{‘6’:‘3’}, 'def]], columns= [‘a’,‘b’])
st.dataframe(df)
