import streamlit as st
import pandas as pd

def enquadramento(val):
    if val < 0:
        return "❌"
    if val > 0:
        return "✅"
    else:
        return ""

df = pd.DataFrame({
    'Name': ['John', 'Mary', 'Petter', 'Anna', 'Tom', 'Jerry'],
    'Total': [-1456.83, 98619.97, -1456.83, 98619.97, -1456.83, 98619.97]
})

st.dataframe(
    df.style.format(precision=2, thousands=".", decimal=",")
        .format(enquadramento, subset=["Total"]),
        column_config={"Total": {"label": "Enqdnt.", "alignment": "center"}, "Name": {"alignment": "center"}},
)
