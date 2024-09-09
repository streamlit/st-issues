import streamlit as st
import pandas as pd
import altair as alt

df = pd.DataFrame(
    {
        "long_column_name_for_tooltip": [0, 1, 2, 3, 4, 5],
        "another_long_column_name": [0, 1, 2, 3, 4, 5],
    }
)
chart = (
    alt.Chart(df)
    .mark_circle()
    .encode(x="long_column_name_for_tooltip", y="another_long_column_name")
)

with st.sidebar:
    st.altair_chart(chart, use_container_width=True)
