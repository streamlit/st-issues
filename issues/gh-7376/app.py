import folium
from streamlit_folium import st_folium
import streamlit as st
from st_aggrid import AgGrid
import pandas as pd



st.title("Location stuff")
tab1, tab2, tab3 = st.tabs(["tab1", "tab2", "tab3"])

with tab1:
  st.text('tab1')

with tab2:
  center = [-36.85605386574607, 174.75310922743114]
  m = folium.Map(location=center, zoom_start=10)
  st_folium(m, width=725)

with tab3:
  df = pd.read_csv('https://raw.githubusercontent.com/fivethirtyeight/data/master/airline-safety/airline-safety.csv')
  AgGrid(df)
