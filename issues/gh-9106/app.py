import streamlit as st
import numpy as np
import pandas as pd

np.random.seed(1)

weather = pd.DataFrame(
    np.c_[
        np.random.uniform(0, 35, 10),
        np.random.uniform(20, 100, 10),
        np.random.uniform(980, 1050, 10),
    ],
    index=pd.date_range(start="20240101", periods=10).date,
    columns=[*"ABC"],
)

colnames = {"A": "Temperature (°C)", "B": "Humidity (%)", "C": "Pressure (hPa)"}

styled_df = (
    weather.style.background_gradient(cmap="coolwarm")
    .set_properties(**{"text-align": "center", "width": "110px"})
    .format_index(colnames.get, axis=1)
)

st.table(styled_df)
st.dataframe(styled_df)
st.html(styled_df.to_html())
