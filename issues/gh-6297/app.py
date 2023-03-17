import streamlit as st

st.title("Right-side label of slider and select_slider overflows when inside expander")

with st.expander('Example st.expander'):

    single_value = st.slider(
        label='Example st.slider',
        min_value=9_500_000,
        max_value=10_000_000,
        value=10_000_000
    )

    first_value,last_value = st.slider(
        label='Example st.slider (range mode)',
        min_value=9_500_000,
        max_value=10_000_000,
        value=(9_500_000,10_000_000)
    )

    single_value = st.select_slider(
        label='Example st.select_slider',
        options=['Maradona','Ronaldo','Pele','This is a very, very long label'],
        value='This is a very, very long label'
        )

    first_value,last_value = st.select_slider(
        label='Example st.select_slider (range mode)',
        options=['Maradona','Ronaldo','Pele','This is a very, very long label'],
        value=['Maradona','This is a very, very long label']
        )
