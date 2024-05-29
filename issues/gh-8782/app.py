import random
import time

import pandas as pd
import plotly.express as px
import streamlit as st

dfData = {'longitude': [0.0], 'latitude': [0.0]}
df = pd.DataFrame(dfData)

mapData = px.scatter_mapbox(df, lat="latitude", lon="longitude", zoom=6, width=400, height=300)
mapData.update_layout(mapbox_style="open-street-map")

latitude = 57.0
longitude = -110.0

mapDisplay = st.empty()
while True:
    latitude += random.uniform(-0.005, 0.005)
    longitude += random.uniform(-0.005, 0.005)
    mapData.data[0].lat = [latitude]
    mapData.data[0].lon = [longitude]
    mapData.update_layout(mapbox_center={"lat": latitude, "lon": longitude})
    mapDisplay.plotly_chart(mapData, use_container_width=True)
    time.sleep(0.1)
