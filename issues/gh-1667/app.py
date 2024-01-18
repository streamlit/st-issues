import altair as alt
from altair.expr import datum
import pandas
import streamlit as st

results=[
    [2016, 11525, 3],
    [2017, 11517, 2],
    [2018, 11521, 2],
    [2019, 11519, 4],
]

dataframe = pandas.DataFrame(
    results,
    columns=["Job Number", "Test Count", "Test Failures"]
)
st.dataframe(dataframe)
base = alt.Chart(dataframe).encode(alt.X('Job Number:O'))
chart_test_count = base.mark_line().encode(alt.Y('Test Count:N'))
chart_test_failures = base.mark_line().encode(alt.Y('Test Failures:N'))

st.write((chart_test_count + chart_test_failures).resolve_scale(y='independent'))
st.altair_chart((chart_test_count + chart_test_failures).resolve_scale(y='independent'))

st.altair_chart(chart_test_count)
st.altair_chart(chart_test_failures)
st.altair_chart(chart_test_count | chart_test_failures)
