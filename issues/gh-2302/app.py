import streamlit as st
import pydeck as pdk

view_state = pdk.ViewState(latitude=0, longitude=0, zoom=2, min_zoom=2)

st.subheader("MapView:")
view = pdk.View(type="MapView", controller=True)
deck = pdk.Deck(views=[view],initial_view_state=view_state)
st.pydeck_chart(deck)

st.subheader("OrbitView:")
view = pdk.View(type="OrbitView", controller=True) 
deck = pdk.Deck(views=[view],initial_view_state=view_state)
st.pydeck_chart(deck)

st.subheader("OrthographicView:")
view = pdk.View(type="OrthographicView", controller=True) 
deck = pdk.Deck(views=[view],initial_view_state=view_state)
st.pydeck_chart(deck)
