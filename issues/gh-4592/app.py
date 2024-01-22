import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

df = []
deck = []
hex_layer = []
scatter_layer = []
view_state = []

for k in range(10):
    df.append(pd.DataFrame(
            np.random.randn(1000, 2) / [50, 50] + [37.76, -122.4],
            columns=['lat', 'lon']
        )
    )
    hex_layer.append(
        pdk.Layer(
           'HexagonLayer',
           data=df[k],
           get_position='[lon, lat]',
           radius=200,
           elevation_scale=4,
           elevation_range=[0, 1000],
           pickable=True,
           extruded=True,
        )
    )
    scatter_layer.append(
        pdk.Layer(
            'ScatterplotLayer',
            data=df[k],
            get_position='[lon, lat]',
            get_color='[200, 30, 0, 160]',
            get_radius=200,
        )
    )
    view_state.append(
        pdk.ViewState(
            latitude=37.76,
            longitude=-122.4,
            zoom=11,
            pitch=50,
        )
    )
    deck.append(
        pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=view_state[k],
            layers=[hex_layer[k], scatter_layer[k]]
        )
    )

    st.pydeck_chart(deck[k])
