import streamlit as st
import numpy as np
import pandas as pd

df = pd.DataFrame(np.random.randn(20, 3), columns=["a", "b", "c"])

st.dataframe(df, height=220)
