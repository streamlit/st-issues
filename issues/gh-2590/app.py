import pandas as pd
import pydeck as pydeck
import streamlit as st

DATA_URL = "https://raw.githubusercontent.com/ajduberstein/geo_datasets/master/small_waterfall.csv"
df = pd.read_csv(DATA_URL)

target = [df.x.mean(), df.y.mean(), df.z.mean()]

point_cloud_layer = pydeck.Layer(
    "PointCloudLayer",
    data=DATA_URL,
    get_position=["x", "y", "z"],
    get_color=["r", "g", "b"],
    get_normal=[0, 0, 15],
    auto_highlight=True,
    pickable=True,
    point_size=3,
)

view_state = pydeck.ViewState(target=target, controller=True, rotation_x=15, rotation_orbit=30, zoom=5.3)
view = pydeck.View(type="OrbitView", controller=True)

r = pydeck.Deck(point_cloud_layer, initial_view_state=view_state, views=[view])
#r.to_html("point_cloud_layer.html", css_background_color="#add8e6")
st.pydeck_chart(r)
