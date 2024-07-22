import streamlit as st

import plotly.graph_objects as go
import pandas as pd
from plotly import data

# import plotly.io as pio
# pio.renderers.default = 'notebook' # fixes error if in VS Code notebook (.ipynb)

df = data.stocks()

layout = dict(
    hoversubplots="axis",
    title="Stock Price Changes",
    hovermode="x",
    grid=dict(rows=3, columns=1),
)

data = [
    go.Scatter(x=df["date"], y=df["AAPL"], xaxis="x", yaxis="y", name="Apple"),
    go.Scatter(x=df["date"], y=df["GOOG"], xaxis="x", yaxis="y2", name="Google"),
    go.Scatter(x=df["date"], y=df["AMZN"], xaxis="x", yaxis="y3", name="Amazon"),
]

fig = go.Figure(data=data, layout=layout)

st.plotly_chart(fig)
