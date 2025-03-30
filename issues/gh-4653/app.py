import streamlit as st
import plotly.graph_objects as go
import numpy as np

# Create sample data for animation
t_values = np.linspace(0, 10, 30)
x = np.cos(t_values)
y = np.sin(t_values)
z = t_values

# Create frames for the animation
frames = [go.Frame(data=[go.Scatter3d(x=[x[k]], y=[y[k]], z=[z[k]], mode='markers',
                                      marker=dict(size=5, color='blue'))],
                   name=f'frame_{k}') for k in range(len(t_values))]

# Initial data
initial_data = go.Scatter3d(x=[x[0]], y=[y[0]], z=[z[0]], mode='markers',
                            marker=dict(size=5, color='red'))

# Create the figure
fig = go.Figure(data=[initial_data], frames=frames)

# Add buttons and sliders
fig.update_layout(
    updatemenus=[{
        'buttons': [
            {
                'args': [None, {'frame': {'duration': 100, 'redraw': True}, 'fromcurrent': True}],
                'label': 'Play',
                'method': 'animate'
            },
            {
                'args': [[None], {'frame': {'duration': 0, 'redraw': True}, 'mode': 'immediate', 'transition': {'duration': 0}}],
                'label': 'Pause',
                'method': 'animate'
            }
        ],
        'direction': 'left',
        'pad': {'r': 10, 't': 87},
        'showactive': False,
        'type': 'buttons',
        'x': 0.1,
        'xanchor': 'right',
        'y': 0,
        'yanchor': 'top'
    }]
)

fig.update_layout(
    sliders=[{
        'steps': [
            {
                'args': [
                    [f'frame_{k}'],
                    {
                        'frame': {'duration': 100, 'redraw': True},
                        'mode': 'immediate',
                        'transition': {'duration': 100}
                    }
                ],
                'label': str(k),
                'method': 'animate'
            } for k in range(len(t_values))
        ],
        'transition': {'duration': 100},
        'x': 0.1,
        'len': 0.9,
        'currentvalue': {'font': {'size': 20}, 'prefix': 'Time:', 'visible': True, 'xanchor': 'right'},
        'pad': {'b': 10, 't': 50},
    }]
)

# Set layout properties
fig.update_layout(
    scene=dict(
        xaxis=dict(range=[-1.5, 1.5]),
        yaxis=dict(range=[-1.5, 1.5]),
        zaxis=dict(range=[0, 10]),
        aspectmode='cube'
    ),
    scene_camera=dict(eye=dict(x=1.25, y=1.25, z=1.25)),
    width=800,
    height=600,
    title="3D Animation Example"
)

# Display the plot
st.plotly_chart(fig, use_container_width=True)
