
import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.subheader("Using st.slider")

if st.session_state.get('fig') is None:
    st.session_state['freq'] = np.arange(0.0, 5.1, 0.1).round(2)    
    f = st.session_state['freq'][2]
    st.session_state['fig'] = go.Figure()
    st.session_state['fig'].add_trace(
        go.Scatter(
            name=str(f),
            x=np.arange(0, 10.01, 0.01),
            y=np.sin(f* np.arange(0, 10.01, 0.01))))
    
def sldier_callback():
    f = st.session_state['slider_freq']
    x = st.session_state['fig'].data[0].x
    st.session_state['fig'].data[0].y = np.sin(f*x)
    st.session_state['fig'].data[0].name = str(f)


f = st.select_slider(
    label='Frequency', 
    options=st.session_state['freq'],
    value=2,
    on_change=sldier_callback,
    key='slider_freq'
)

st.plotly_chart(st.session_state['fig'])

st.subheader("Using plotly slider")

import plotly.graph_objects as go
import numpy as np


fig = go.Figure()
for step in np.arange(0, 5, 0.1):
    fig.add_trace(
        go.Scatter(
            visible=False,
            name="f = " + str(step),
            x=np.arange(0, 10, 0.01),
            y=np.sin(step * np.arange(0, 10, 0.01))))

fig.data[10].visible = True

# Create and add slider
steps = []
for i in range(len(fig.data)):
    step = dict(
        method="update",
        args=[              
            {"visible": [False] * len(fig.data)},
            {"title": "Slider switched to step: " + str(i)}],  
    )
    step["args"][0]["visible"][i] = True
    steps.append(step)

sliders = [dict(
    active=10,
    currentvalue={"prefix": "Frequency: "},
    pad={"t": 50},
    steps=steps
)]

fig.update_layout(
    sliders=sliders
)

st.plotly_chart(fig)
