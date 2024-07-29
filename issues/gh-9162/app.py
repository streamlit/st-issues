import streamlit as st
import pandas as pd
import plotly.express as px

st.write(f'Streamlit {st.__version__}')
df = pd.DataFrame({'x': [1, 2, 3], 'y': [10, 18, 13]})
g = px.bar(df, x='x', y='y')
st.plotly_chart(g, use_container_width=False)
st.plotly_chart(g, use_container_width=True)
