import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Sample data
data = {
    "Category": ["A", "B", "C"],
    "Value1": [10, 20, 15],
    "Value2": [5, 12, 8],
    "Value3": [8, 15, 22],
}
df = pd.DataFrame(data)

# Create the stacked bar chart
fig = go.Figure(
    data=[
        go.Bar(name="Value1", x=df["Category"], y=df["Value1"]),
        go.Bar(name="Value2", x=df["Category"], y=df["Value2"]),
        go.Bar(name="Value3", x=df["Category"], y=df["Value3"]),
    ]
)

# Update the layout for stacked bars
fig.update_layout(barmode="stack", title="Stacked Bar Chart Example")

st.plotly_chart(fig, use_container_width=True)
