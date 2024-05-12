import altair as alt
import streamlit as st
from vega_datasets import data
source = data.barley()
chart = alt.Chart(source).mark_bar().encode(
    color="year:O",
    x="yield",
    y="variety",
    yOffset="site",
)
st.altair_chart(chart)
