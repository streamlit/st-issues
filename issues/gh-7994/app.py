import altair as alt
import streamlit as st
import pandas as pd

make = pd.DataFrame({'name': ['Honda', 'Ford', 'Dodge']})
fuel = pd.DataFrame({
    'Honda': [9, 8, 8, 7, 7],
    'Ford': [5, 4, 3, 2, 1],
    'Dodge': [6, 5, 5, 3, 4]
}).reset_index().melt(id_vars=['index'], var_name='name', value_name='fuel')

selection = alt.selection_multi(fields=['name'])
color = alt.condition(selection, alt.Color('name:N'), alt.value('lightgray'))
make_selector = alt.Chart(make).mark_rect().encode(y='name', color=color).add_selection(selection)
fuel_chart = alt.Chart(fuel).mark_line().encode(x='index', y=alt.Y('fuel', scale=alt.Scale(domain=[0, 10])), color='name').transform_filter(selection)

# creating compound chart here
chart=st.altair_chart(make_selector|fuel_chart,use_container_width=True)

# this line should add data and does not work
chart.add_rows(pd.DataFrame({'index':[5]*3,'name':['Honda', 'Ford', 'Dodge'],'fuel':[8,2,5]}))
