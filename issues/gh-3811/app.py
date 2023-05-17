import streamlit as st
import pandas as pd

hi = {"ints": [-1, -2, 3, 4], "strings":['-2', '-3', '4', '5']}
data = pd.DataFrame(hi)

st.dataframe(data)
