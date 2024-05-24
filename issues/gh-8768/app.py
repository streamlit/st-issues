import streamlit as st
import plotly.express as px
import pandas as pd


@st.cache_data(ttl="5h", show_spinner=False)
def linechart(plot_df: pd.DataFrame, x_label: str, y_label: str):
    fig = px.line(plot_df)
    fig.update_layout(xaxis_title=x_label, yaxis_title=y_label)
    st.plotly_chart(fig, use_container_width=True)


plot_df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [10, 15, 13, 17]})


linechart(plot_df, "x", "y")
