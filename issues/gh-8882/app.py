import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.title("3D Plot with Plotly in Streamlit")

st.sidebar.header("3D Plot Controls")
x_range = st.sidebar.slider("X-axis range", -10, 10, (-5, 5))
y_range = st.sidebar.slider("Y-axis range", -10, 10, (-5, 5))
z_func = st.sidebar.selectbox(
    "Z function",
    ("sin(x) * cos(y)", "cos(x) * sin(y)", "x^2 - y^2")
)

x = np.linspace(x_range[0], x_range[1], 100)
y = np.linspace(y_range[0], y_range[1], 100)
x, y = np.meshgrid(x, y)

if z_func == "sin(x) * cos(y)":
    z = np.sin(x) * np.cos(y)
elif z_func == "cos(x) * sin(y)":
    z = np.cos(x) * np.sin(y)
else:
    z = x**2 - y**2

fig = go.Figure(data=[go.Surface(z=z, x=x, y=y)])

# uirevision should enable the camera view to persist across user interactions
fig.update_layout(
    title=f"3D Plot of {z_func}",
    scene=dict(
        xaxis_title='X Axis',
        yaxis_title='Y Axis',
        zaxis_title='Z Axis',
    ),
    margin=dict(l=65, r=50, b=65, t=90),
    uirevision='const'
)

st.plotly_chart(fig, use_container_width=True)
