import pandas as pd
import streamlit as st

st.write(pd.Series(pd.qcut(range(5), 4)))
