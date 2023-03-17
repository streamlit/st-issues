import numpy as np
import streamlit as st
import time
import pandas as pd

'''
streamlit == 1.18.1
pandas == 1.5.0
'''

@st.cache_data()
def get_data():
    df = pd.DataFrame({"num":[112,112,2,3],"str":['be','a','be','c']})
    return df

@st.cache_data()
def show_data(data):
    time.sleep(1)
    return data

df = get_data()
data = df['str'].unique()

index_daily_data = show_data(data)
st.dataframe(index_daily_data)
st.button("rerun")
