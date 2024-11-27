import pydeck as pdk
import pandas as pd

COUNTRIES = "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_scale_rank.geojson"
view_state = pdk.ViewState(latitude=51.47, longitude=0.45, zoom=2, min_zoom=0)

# Set height and width variables
view = pdk.View(type="_GlobeView", controller=True, width=1000, height=700)
layers = [
    pdk.Layer(
        "GeoJsonLayer",
        id="base-map",
        data=COUNTRIES,
        stroked=False,
        filled=True,
        get_fill_color=[200, 200, 200],
    )
]

deck = pdk.Deck(
    views=[view],
    initial_view_state=view_state,
    tooltip={"text": "{name}, {primary_fuel} plant, {country}"},
    layers=layers,
    map_provider=None,
    # Note that this must be set for the globe to be opaque
    parameters={"cull": True},
)

deck.to_html("globe_view.html", css_background_color="black")

import streamlit as st
st.pydeck_chart(deck)
