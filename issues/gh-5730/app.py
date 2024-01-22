import plotly.graph_objects as go
import streamlit as st

fig = go.Figure()
fig.add_table(
    header=dict(values=["Header1", "Header2 with space"]),
    cells=dict(
        values=[
            ["text with spaces"] * 30,
            ["text_without_spaces"] * 30,
        ],
    ),
)
tab1, tab2 = st.tabs(["Tab1", "Tab2"])
tab1.button("Get text back")
tab1.plotly_chart(fig)

with tab2:
    st.button("Click on button and text tab 1 disappears")
