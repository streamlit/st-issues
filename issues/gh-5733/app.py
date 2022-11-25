import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data

temps = data.seattle_temps()
temps = temps[ temps.date.dt.hour == 10 ]

startDate = pd.to_datetime("2010-06-01")
endDate = pd.to_datetime("2010-06-30")
myScale = alt.Scale(domain=[startDate, endDate], )

c = alt.Chart(temps).mark_line(clip=True).encode(
    x=alt.X('date:T', scale=myScale),
    y='temp:Q'
)

st.altair_chart( c )

c.show()