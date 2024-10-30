import pandas as pd
import streamlit as st

df = pd.DataFrame([[pd.Timedelta(seconds=1), pd.Timestamp(0) + pd.Timedelta(seconds=1)]], columns=['A', 'B'])
st.dataframe(df, column_config={c: st.column_config.TimeColumn(c) for c in ['A', 'B']})
st.markdown(str(df))
st.dataframe(df.dtypes)
st.dataframe(df)
