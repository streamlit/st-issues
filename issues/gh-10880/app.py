import streamlit as st
import pandas as pd

df = pd.DataFrame(
    {"Index": ["X", "Y", "Z"], "A": [1, 2, 3], "B": [6, 5, 4], "C": [9, 7, 8]}
)
df = df.set_index("Index")
st.dataframe(df)
st.dataframe(df.T.corr())
st.dataframe(df.T.corr().unstack())
print(df.T.corr().unstack())
