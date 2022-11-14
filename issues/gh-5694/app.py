import streamlit as st
import pandas as pd

df = pd.DataFrame()
with st.expander("Test"):
    st.dataframe(df, use_container_width=True)
