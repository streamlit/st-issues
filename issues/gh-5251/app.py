import streamlit as st
import plotly.express as px

fig = px.scatter(x=[0, 1, 2, 3, 4], y=[0, 1, 4, 9, 16],
                 labels={'x':r"$x \to x^2$", 'y':"$x^2$"})

st.plotly_chart(fig) # No latex rendered
st.plotly_chart(fig,include_mathjax="cdn") # No latex rendered either
st.markdown(r"$x \to x^2$") # But streamlit latex (KaTex?) does work
