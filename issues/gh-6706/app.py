import streamlit as st
import pandas as pd

df = pd.DataFrame({
    'A':[1,2,3,4],
    'B':[1111,2,33,44444],
    'C':[1,2,3,4]
})

styled_df = df.style.set_properties(**{
    "background-color": "white",
    "color": "black",
    "border-color": "black",
    'text-align': 'center'
})

st.dataframe(styled_df)
st.table(styled_df)
