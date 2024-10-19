import pandas as pd
import streamlit as st

# Create a DataFrame with specified indices and columns
data = {
    "col1": [1.0, 2.0, 3.0],
    "col2": [4.0, 5.0, 6.0],
    "group": ["A", "B", "C"],
}
index = ["group1", "group2", "group3"]

df = pd.DataFrame(data).set_index("group")

st.data_editor(
    df,
    hide_index=False,
    column_config={"group": st.column_config.TextColumn(disabled=True)},  # noqa
)
