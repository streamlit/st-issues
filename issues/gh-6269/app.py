import streamlit as st
import altair as alt

chart = alt.Chart(pd.DataFrame(dict(x=list(range(10)),y=list(range(10))))).mark_line().encode(
    x=alt.X('x'),
    y=alt.Y('y'),
)
st.altair_chart(alt.Chart.from_json(chart.to_json()))
