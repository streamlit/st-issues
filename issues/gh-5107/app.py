import numpy as np
import streamlit as st
from plotly.graph_objects import Figure, Scatter

# Add a "useless" button just to be able to rerun app with a click and see if uirevision works
st.button("Rerun app")

# Generate random data
if "x1" not in st.session_state:
    st.session_state.x1 = np.random.randn(200) - 2
    st.session_state.x2 = np.random.randn(200)

# Create figure
fig = Figure()
fig.add_trace(Scatter(x=st.session_state.x1, y=st.session_state.x2, name="Raw data"))

# Add uirevision parameter to fig
fig.update_layout({"uirevision": "foo"}, overwrite=True)

# Plot
st.plotly_chart(fig, use_container_width=True)
