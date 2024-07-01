import streamlit as st
import plotly.express as px

df = px.data.gapminder().query("year == 2007")

fig = px.treemap(
    df,
    path=["continent", "country"],
    values="pop",
)

event_dict = st.plotly_chart(fig, on_select="rerun")

st.write(event_dict)
