import streamlit as st
import plotly.graph_objects as go

fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=["A", "B", "C", "D"],
        color="blue"
    ),
    link=dict(
        source=[0, 1, 0, 2, 3],
        target=[2, 3, 3, 3, 0],
        value=[8, 4, 2, 8, 4]
    )
)])

fig.update_layout(
    title="Sankey Diagram Example",
    font_family="Times New Roman",
    font_color="blue",
    font_size=14  # This is the only setting that works
)

st.plotly_chart(fig)  # Font family and color are ignored
# fig.show()          # Shows correct font and color
