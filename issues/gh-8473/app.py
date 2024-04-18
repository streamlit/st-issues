import pandas as pd
import streamlit as st

df = pd.DataFrame(
    [
        ["A", "B", "C"],
        ["D", "E", "F"],
        ["G", "H", "I"],
    ],
    columns=range(3, 0, -1)

df = st.data_editor(
    df,
    column_config={
        col: st.column_config.TextColumn(
            col,
        )
        for col in df.columns
    },
)
