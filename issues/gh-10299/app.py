import streamlit as st
import pandas as pd

svg = \
"""<svg xmlns='http://www.w3.org/2000/svg'>
<g transform='translate(0 -1)' fill='none'>
<circle fill='#CAC5C0' cx='50' cy='50.998' r='50'/><path d='M55.685 11.001v64.108c0 7.671 3.226 11.504 9.687 11.504h1.684v4.388h-34.111v-4.388h2.141c6.247 0 9.369-3.833 9.369-11.504v-42.054c0-7.758-2.697-11.643-8.081-11.643h-3.429v-4.247h1.237c6.66 0 12.691-2.057 18.08-6.165l3.423.001z' fill='#0D0F0F'/></g></svg>
"""

svg_works = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'%3E%3Cg transform='translate(0 -1)' fill='none'%3E%3Ccircle fill='%23CAC5C0' cx='50' cy='50.998' r='50'/%3E%3Cpath d='M55.685 11.001v64.108c0 7.671 3.226 11.504 9.687 11.504h1.684v4.388h-34.111v-4.388h2.141c6.247 0 9.369-3.833 9.369-11.504v-42.054c0-7.758-2.697-11.643-8.081-11.643h-3.429v-4.247h1.237c6.66 0 12.691-2.057 18.08-6.165l3.423.001z' fill='%230D0F0F'/%3E%3C/g%3E%3C/svg%3E"
st.image(svg)

svg = f'data:image/svg+xml;utf8,{svg}' #according to https://docs.streamlit.io/develop/api-reference/data/st.column_config/st.column_config.imagecolumn
df = pd.DataFrame({"img": [svg_works]})
st.dataframe(
    df,
    column_config={
    'img':st.column_config.ImageColumn('svg_test', width='large'),
},
    hide_index=True
)
