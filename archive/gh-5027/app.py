import pandas as pd
import streamlit as st

metric = pd.Series([24, 67, 36, 489, 28, 389, 390])
metric_df = pd.cut(metric, 2).to_frame()
# st.dataframe(metric_df)
# st.dataframe(metric_df.value_counts())
# st.table(metric_df)
st.table(metric_df.value_counts())
