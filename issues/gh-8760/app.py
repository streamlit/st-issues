import streamlit as st
import numpy as np
import plotly.express as px

# make a 2d array of size 10x20
np.random.seed(0)
data = np.random.randn(10, 20)

# make a plotly figure of this data, show selection
fig = px.imshow(data)
fig.update_layout(dragmode="drawrect")
selection = st.plotly_chart(fig, on_select="rerun")
st.json(selection)
