import streamlit as st
import pandas as pd

# Sample DataFrame with latitude, longitude, color, and size columns
data = {
    'latitude': [34.0522, 37.7749, 40.7128],
    'longitude': [-118.2437, -122.4194, -74.0060],
    'color': ['#0044ff', '#FF0000', '#008000'],
    'size': [10, 20, 15]
}

df = pd.DataFrame(data, index=[1, 2, 3])

st.map(df, color='color')
