import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go

import streamlit as st

df = pd.DataFrame({
    "id": ["A", "B", "C", "D", "E"],
    "data1": [124, 12, 473, 219, 122],
    "stack1": [234, 346, 124, 743, 586],
    "stack2": [586, 24, 346, 235, 584],
    "stack3": [456, 34, 243, 745, 423]
})

st.dataframe(df)

fig = make_subplots(rows = 3, cols = 1, shared_xaxes = True)

fig.add_trace(
    go.Bar(
        x = df.id,
        y = df.data1
    ),
    row = 1,
    col = 1
)


bars = []
for _, row in df.iterrows():
    for i in [1, 2, 3]:
        bars.append(
            go.Bar(
                x = [row.id],
                y = [row[f"stack{i}"]]
            )
        )

fig.add_traces(bars, rows = 2, cols = 1)
fig.update_layout(hovermode = "x unified",
                  barmode = 'stack')

s = st.plotly_chart(fig, on_select = "rerun")

st.json(s)
