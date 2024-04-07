import streamlit as st

import plotly.express as pltx
import plotly.graph_objects as go

x = [16777217 + x for x in range(20)]
y = x

fig = pltx.scatter(x=x, y=y, render_mode='webgl')
st.plotly_chart(fig)

fig = pltx.scatter(x=x, y=y, render_mode='svg')
st.plotly_chart(fig)
