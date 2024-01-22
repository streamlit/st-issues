import streamlit as st
import pandas as pd
import plotly.graph_objects as go

df = pd.DataFrame({'X': [1, 2, 3, 4, 5], 'Y': [10, 14, 18, 24, 30]})

# fail to update streamlit font
st.header('Update font via update_layout()')
fig = go.Figure()
fig.add_trace(go.Scatter(x=df['X'], y=df['Y'], mode='lines+markers', name='Line Plot'))
fig.update_layout(
    title="Line (big font size 24)",
    xaxis_title="X",
    yaxis_title="Y",
    font=dict(size=24),
)
st.plotly_chart(fig)

# confirm this font-update works in base plotly
fig.show()

# succesfully update streamlit font
st.header('Update font via plotly graph object')
fig_two = go.Figure()
fig_two.update_yaxes(tickfont=dict(family="Lucida Console",
                               size= 24,
                               color='red'))
st.plotly_chart(fig_two)
