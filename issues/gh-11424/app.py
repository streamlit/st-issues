import streamlit as st
import plotly.express as px

for i in range(10):
    df = px.data.iris()
    fig = px.scatter(
        df,
        x="sepal_width",
        y="sepal_length",
        color="species",
        size="petal_length",
        hover_data=["petal_width"],
    )
    st.plotly_chart(fig)
