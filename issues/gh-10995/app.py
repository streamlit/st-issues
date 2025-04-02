import pandas as pd
import plotly.graph_objects as go
import streamlit as st

is_stacked = st.checkbox("Render as Stacked?", value=True)

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

# Update the layout for stacked bars based on user input
barmode = "stack" if is_stacked else None

fig.update_layout(
    title="Stacked Bar Chart Example",
    barmode=barmode,
    xaxis_title="Category",
    yaxis_title="Value",
    height=400,
    margin=dict(t=40, b=20, l=20, r=20),
    xaxis=dict(
        type="category",
        categoryorder="array",
        categoryarray=sorted(df["Category"].unique()),
    ),
    paper_bgcolor="rgba(255,255,255,0)",
    plot_bgcolor="rgba(247,247,247,0.5)",
)

st.plotly_chart(fig, use_container_width=True)
