# create a very basic alt.chart
import streamlit as st
import altair as alt
import pandas as pd

# Create a simple dataframe
df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

# Create a simple chart
chart = (
    alt.Chart(
        data=df,
        title="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed nec purus euismod, ultricies nunc nec, ultricies nunc.",
    )
    .mark_line()
    .encode(x="x", y="y")
)

# Render the chart
st.altair_chart(chart, use_container_width=True)
st.altair_chart(chart, use_container_width=False)
