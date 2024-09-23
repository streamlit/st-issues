import streamlit as st
import plotly.graph_objects as go
import plotly.express as px


st.title("Some Title")

# example from https://plotly.com/python/tile-scatter-maps/#basic-example-with-plotly-express
df = px.data.carshare()
fig = px.scatter_map(
    df,
    lat="centroid_lat",
    lon="centroid_lon",
    color="peak_hour",
    size="car_hours",
    color_continuous_scale=px.colors.cyclical.IceFire,
    size_max=15,
    zoom=10,
)
st.plotly_chart(fig, use_container_width=True)
