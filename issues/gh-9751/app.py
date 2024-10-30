import pandas as pd
import streamlit as st

st.dataframe(pd.DataFrame([[pd.Timedelta(seconds=1), pd.Timestamp(0) + pd.Timedelta(seconds=1)]], columns=['A', 'B']),
             column_config={c: st.column_config.TimeColumn(c) for c in ['A', 'B']})
