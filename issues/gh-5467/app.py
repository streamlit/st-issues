import altair as alt
import streamlit as st
from vega_datasets import data

iris = data.iris()

iris_chart = (
    alt.Chart(iris)
    .mark_point()
    .encode(
        x="petalWidth",
        y="petalLength",
        color=alt.Color(
            "species",
            legend=alt.Legend(title=None, titlePadding=0, offset=10, orient="top"),
        ),
    )
)

st.altair_chart(iris_chart, use_container_width=True)
