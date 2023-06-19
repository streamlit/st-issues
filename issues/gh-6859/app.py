import streamlit as st
import pandas as pd
import time

if "df" not in st.session_state:
    with st.spinner("Load data"):
        time.sleep(5)
        df = pd.DataFrame({"A": [1, 2, 3]})
        st.session_state.df = df

st.dataframe(st.session_state.df)

# Do something else that takes some time:
time.sleep(5)
