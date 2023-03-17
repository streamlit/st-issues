import streamlit as st
import pandas as pd
import numpy as np
'''
streamlit 1.19.0
pandas 1.5.3
'''
df = pd.DataFrame({'a':[1,2,3],'b':[1,2,3],'c':[1,2,3]})

@st.cache_data
def show(df):
    return df

st.code("""
@st.cache_data
def show(df):
    return df
""")

columns_name = st.text_input("New column name")

if columns_name:
    try:
        df.columns = columns_name.split(",")
    except:
        df.columns = ['A','B','C']
        st.error('Invalid, please enter three column names separated by commas, such as "q, w, e".')

if st.button('add a column'):
    df['new'] = 4

st.write("st.dataframe(df)")
st.dataframe(df)

st.write("st.dataframe(show(df))")
st.dataframe(show(df))
