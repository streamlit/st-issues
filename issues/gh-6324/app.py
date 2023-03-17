import pandas as pd
import streamlit as st
import plotly.express as px

df = pd.DataFrame([[1, 2, 3], [4, 5, 6]])

st.plotly_chart(px.line(df),
                use_container_width=True  # Makes bug more obvious
                )
