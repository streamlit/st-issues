import streamlit as st
import plotly.express as px
from skimage import data
import plotly.graph_objects as go

st.title("zoom scroll bug")

config = {"scrollZoom": True}
img = data.astronaut()
fig = px.imshow(img, binary_format="jpeg", binary_compression_level=0)
st.plotly_chart(fig, config=config)
fig.show(config=config)
