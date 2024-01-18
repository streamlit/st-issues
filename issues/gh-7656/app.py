import streamlit as st
import pandas as pd
import pydeck as pdk

@st.cache_data
def from_data_file(filename):
    url = (
        "https://raw.githubusercontent.com/streamlit/"
        "example-data/master/hello/v1/%s" % filename
    )
    return pd.read_json(url)

colour = st.radio(
    "Select Colour:",
    ["[200, 30, 0, 160]", "[180, 0, 200, 140]"])

st.pydeck_chart(pdk.Deck(
    map_style=None,
    initial_view_state=pdk.ViewState(
        latitude=37.76,
        longitude=-122.4,
        zoom=11,
        pitch=50,
    ),
    layers=[
        pdk.Layer(
            "ScatterplotLayer",
            data=from_data_file("bart_stop_stats.json"),
            get_position=["lon", "lat"],
            get_color=colour,
            get_radius="[exits]",
            radius_scale=0.05,
        ),
    ]
))
