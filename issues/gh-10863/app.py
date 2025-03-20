import numpy as np
import pandas as pd
import streamlit as st

df1 = pd.DataFrame(np.random.randint(0, 100, size=(100_000, 4)), columns=list("ABCD"))
st.dataframe(df1)

df2 = pd.DataFrame(np.random.randint(0, 100, size=(1_000_000, 4)), columns=list("ABCD"))
st.dataframe(df2)
