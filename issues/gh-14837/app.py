import pandas as pd
import streamlit as st

df = pd.DataFrame(
    {"c": [10, 10]},
    index=[
        "Lorem ipsum dolor",
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore.",
    ],
)

c1, _ = st.columns(2)
c1.dataframe(df, width="content")
