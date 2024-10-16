import streamlit as st
import pandas as pd

data = [["a", 1], ["b", 2]]
df = pd.DataFrame(data, columns=["x", "y"])
df["x"] = pd.Categorical(df["x"], categories=["a", "b"])
st.dataframe(df.set_index("x"))
