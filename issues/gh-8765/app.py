import altair as alt
from vega_datasets import data

import streamlit as st
import pandas as pd


df = pd.read_json(data.cars.url)

input_dropdown = alt.binding_radio(
    options=df.Origin.unique().tolist(),
    labels=df.Origin.unique().tolist(),
    name='Region: '
)

single_selection = alt.selection_point(name="single", toggle=False)
selection = alt.selection_point(
    name = 'og_select',
    fields=['Origin'], bind=input_dropdown, value = df.Origin.unique().tolist()[0], toggle = False
)
chart = (
    alt.Chart(data.cars.url)
    .mark_point(
        tooltip=True,
    )
    .encode(
        x="Miles_per_Gallon:Q",
        y="Horsepower:Q",
        color=alt.condition(single_selection, "Origin:N", alt.value("lightgray")),
    ).transform_filter(
       selection
    ).add_params(
        single_selection,
        selection
    )
        
    
)

return_event = st.checkbox('Use selection')
if return_event:
    event_data = st.altair_chart(
        chart, on_select="rerun", selection_mode = 'single', 
        use_container_width=True)
    st.write(event_data)
else:
    st.altair_chart(
        chart, 
        use_container_width=True
    )
