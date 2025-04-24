from PIL import Image
import streamlit as st
import plotly.graph_objects as go

image: Image.Image = Image.open(r"issues/gh-11178/test.png")

fig = go.Figure(data=[go.Image(z=image)])
# OR
# fig = go.Figure()
# fig.add_trace(go.Image(z=image))

st.plotly_chart(fig)
