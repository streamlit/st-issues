import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide")  # Not required, but makes bug more obvious, since every resize then affects the plot

df = pd.DataFrame([[1, 2, 3], [4, 5, 6]])

st.plotly_chart(px.line(df),
                use_container_width=True  # Makes bug more obvious
                )
