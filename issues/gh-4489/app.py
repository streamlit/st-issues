import pandas as pd
import streamlit as st

s = pd.Series(pd.date_range("2012-1-1", periods=3, freq="D"))

td = pd.Series([pd.Timedelta(days=i) for i in range(3)])

df = pd.DataFrame(
    {
        "A": s,
        "B": td
    }
)

st.dataframe(df)
