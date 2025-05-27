import plotly.express as px
import streamlit as st

data_canada = px.data.gapminder().query("country == 'Canada'")
fig = px.bar(data_canada, x="year", y="pop")

st.plotly_chart(fig)
