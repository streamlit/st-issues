import streamlit as st
import pandas as pd

@st.cache_resource
def get_value(df):
    import random
    return random.random()


df1 = pd.DataFrame({'A': [1], 'B': [2]})
df2 = pd.DataFrame({'A': [1], 'C': [2]})

# See that these two are the same value, despite the dataframes clearly being different
# in a way that is easily checkable -- just hash the headers too!
st.write(get_value(df1))
st.write(get_value(df2))
