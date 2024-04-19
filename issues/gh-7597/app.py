import streamlit as st
import pandas as pd
import plotly.express as px

with st.sidebar:
    # option to show or hide figure 1
    show_fig_1 = st.checkbox("show_fig_1", True, key="show_fig_1")

data = {"a": [1, 2, 3], "b": [1, 4, 9]}
df = pd.DataFrame(data)

if show_fig_1:
    st.header("Figure 1")
    fig_1 = px.line(df, x="b", y="a")
    fig_1.update_layout(height=1000)
    st.plotly_chart(fig_1, use_container_width=True)

st.header("Figure 2")
fig_2 = px.line(df, x="a", y="b")
# when show_fig_1 is unselected the height is 1000 and use_container_width becomes True
st.plotly_chart(fig_2, use_container_width=False)
