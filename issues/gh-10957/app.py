import pandas as pd
import streamlit as st


@st.cache_data
def get_df1():
    df1 = pd.DataFrame({"col": [[1, 2]]}, index=[1])
    print(df1)
    return df1


@st.cache_data
def get_df2(df1):
    df2 = pd.DataFrame({"col2": [42]}, index=[1])
    print(df2)

    return pd.merge_asof(df1, df2, left_index=True, right_index=True)


df1 = get_df1()
df2 = get_df2(df1)
st.write(df2)
