import streamlit as st
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

np.random.seed(0)
dates = pd.date_range(start='2023-01-01', periods=100)
balances = np.random.randn(100).cumsum()
expenses = np.random.randn(100).cumsum()

df = pd.DataFrame({'Date': dates, 'Balance': balances, 'Expenses': expenses})

fig = make_subplots(specs=[[{"secondary_y": False}]])

fig.add_trace(go.Scatter(
    x=df['Date'], y=df['Balance'],
    mode='lines',
    name='Balance'
))

fig.add_trace(go.Scatter(
    x=df['Date'], y=df['Expenses'],
    mode='lines',
    name='Expenses'
))

# Example data and layout settings
fig.update_layout(
    height=800,
    width=1200,
    autosize=False,  # Prevent Plotly from auto-resizing
    title_text="Daily Balance and Expenses",
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1,
                     label="1m",
                     step="month",
                     stepmode="backward"),
                dict(count=3,
                     label="3m",
                     step="month",
                     stepmode="backward"),
                dict(count=6,
                     label="6m",
                     step="month",
                     stepmode="backward"),
                dict(count=3,
                     label="QTD",
                     step="month",
                     stepmode="todate"),
                dict(count=1,
                     label="YTD",
                     step="year",
                     stepmode="todate"),
                dict(count=1,
                     label="1y",
                     step="year",
                     stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(
            visible=True
        ),
        type="date"
    ),
    yaxis=dict(
        fixedrange=False  # Allow y-axis to rescale dynamically
    )
)
fig.update_yaxes(autorange=True)

st.plotly_chart(fig, use_container_width=False)
