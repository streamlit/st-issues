import pandas as pd
import numpy as np
import altair as alt
import streamlit as st

x = np.linspace(10,100, 10)
y1 = 5*x
y2 = 1/x

df1 = pd.DataFrame.from_dict({'x': x,'y1': y1, 'y2': y2})

c1 = alt.Chart(df1).mark_line(
).encode(
    alt.X('x'),
    alt.Y('y1')
)

c2 = alt.Chart(df1).mark_line(
).encode(
    alt.X('x'),
    alt.Y('y2')
)

#Individual, Static Charts
st.altair_chart(c1, use_container_width = True)
st.altair_chart(c2, use_container_width = True)

#Concatenated Charts with shared zoom function
zoom = alt.selection_interval(bind = 'scales', encodings = ['x'])
st.altair_chart(c1.add_selection(zoom) & c2.add_selection(zoom), use_container_width = True)
