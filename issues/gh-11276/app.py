import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

if 'value1' not in st.session_state:
    st.session_state['value1'] = np.random.randint(1, 100, size=20)
    st.session_state['value2'] = np.random.randint(1, 100, size=20)
    
df = pd.DataFrame({})
df['date'] = pd.date_range(start='2025-01-01', periods=20, freq='ME').date
df['value1'] = st.session_state['value1']
df['value2'] = st.session_state['value2']
c1, c2 = st.columns([1, 1], gap='small', vertical_alignment='bottom')
c1.dataframe(df, height=200, use_container_width=True, hide_index=True)
fig = px.bar(df, x='date', y=['value1', 'value2'], barmode='group', height=300, text_auto=True, color_discrete_sequence=px.colors.qualitative.Bold)
selected_point = c2.plotly_chart(fig, use_container_width=True, on_select='rerun', selection_mode='points')
selected_point
