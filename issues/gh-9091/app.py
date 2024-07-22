import streamlit as st
import altair as alt
from vega_datasets import data

source = data.cars()

chart = alt.Chart(source, width=100, height=100).mark_point().encode(
    x="Horsepower:Q",
    y="Miles_per_Gallon:Q",
)

st.altair_chart(chart.facet(column="Origin:N"), use_container_width=True)

with st.echo():
    st.altair_chart(chart.facet(column="Origin:N"), use_container_width=True)
with st.echo():
    st.altair_chart(chart.encode(column="Origin:N"), use_container_width=True)
with st.echo():
    st.altair_chart(chart.facet(row="Origin:N"), use_container_width=True)
with st.echo():
    st.altair_chart(chart.encode(row="Origin:N"), use_container_width=True)
