import pandas as pd
import streamlit as st

names = ["John","Sarah","Jane"]
years = list(range(1,4))
distances = pd.DataFrame(0,names,years)
new_distances = st.data_editor(distances,key="new_distances")
