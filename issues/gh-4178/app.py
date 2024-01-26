import plotly.express
import streamlit as st
import pandas as pd
import plotly.io as pio

theme_select_option = st.selectbox(label='Plotly theme', options=pio.templates.keys())

st.plotly_chart(
    plotly.express.line(
        pd.Series(
            data=[89, 86, 88, 84, 65, 90, 89, 120, 88, 84, 85, 89, 90, 89, 120, 88, 84, 85, 89, 60],
        ),
        template=theme_select_option,
    )
)
