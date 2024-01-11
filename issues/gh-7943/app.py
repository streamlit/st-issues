import streamlit as st
import pandas as pd

# Sample DataFrame with latitude, longitude, color, and size columns
data = {
    'latitude': [34.0522, 37.7749, 40.7128],
    'longitude': [-118.2437, -122.4194, -74.0060],
    'color': ['#0044ff', '#0044ff', '#0044ff'],
    'size': [10, 20, 15]
}

df = pd.DataFrame(data)

# Display the map with colored and sized markers
st.map(df, size="size", color="color")

# Sample DataFrame with latitude, longitude, color, and size columns
data = {
    'latitude': [34.0522, 37.7749, 40.7128],
    'longitude': [-118.2437, -122.4194, -74.0060],
    'color': ['red', 'green', 'blue'],
    'size': [10, 20, 15]
}

df = pd.DataFrame(data)

# Display the map with colored and sized markers
st.map(df, size="size", color="color")
