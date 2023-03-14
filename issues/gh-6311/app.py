import pandas as pd
import streamlit as st

df = pd.DataFrame({"a": [1009513310189256287, 2], "b": [11, 22]})

st.dataframe(df)
st.markdown(df.to_html(), unsafe_allow_html=True)
