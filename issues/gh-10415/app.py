import pandas as pd
import streamlit as st

df_regular = pd.DataFrame({"Example": [1, 2, 3], "Example (1)": [4, 5, 6]})

multi_index = pd.MultiIndex.from_tuples([("Test", "Example"), ("Test", "Example (1)")])
df_multi = pd.DataFrame(df_regular.values, columns=multi_index)

st.dataframe(df_regular)
st.dataframe(df_multi)
