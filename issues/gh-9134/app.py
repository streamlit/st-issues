import pandas as pd
import streamlit as st
import plotly.graph_objects as go

df = pd.DataFrame({
        "id": ["A", "B", "C", "D", "E"],
        "data1": [1, 2, 3, 4, 5],
    })

st.dataframe(df)
fig = go.Figure()
fig.add_trace(
    go.Line(
        x = df.id,
        y = df.data1
    ),
)
s = st.plotly_chart(
    fig,
    config=dict(
        scrollZoom=True,  # successfully enabled
        modeBarButtonsToRemove=[
            "zoomOut2d",  # successfully removed
        ],
        modeBarButtonsToAdd=[
            "drawline",  # annotation tool not added
            "drawrect",  # annotation tool not added
            "eraseshape",  # annotation tool not added
        ],
    ),
)
