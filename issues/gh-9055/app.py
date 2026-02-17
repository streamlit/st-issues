import altair as alt
import pandas as pd
import streamlit as st


def update_table():
    if st.session_state.data['value'][0] == 0:
        st.session_state.data['value'] = 1
    else:
        st.session_state.data['value'] = 0


if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame.from_dict(
        {
            'x': [1, 1, 2, 2],
            'y': [1, 2, 1, 2],
            'value': [0, 0, 0, 0],
        }
    )

interval_selector = alt.selection_interval()
chart = (
    alt.Chart(st.session_state.data)
    .mark_point(filled=True, size=1000)
    .encode(
        x='x:O',
        y='y:O',
        color=alt.Color('value:N').scale(domain=[0, 1], range=['blue', 'red']),
    )
    .properties(width=600, height=350)
    .add_params(interval_selector)
)

st.header('space filler to see jump')
st.header('...')
st.header('...')
st.header('...')
st.header('...')
st.header('...')

st.dataframe(pd.DataFrame())  # uncommenting this line causes view to jump when interacting with chart

st.altair_chart(chart,
                theme=None,
                on_select=update_table,
                key='chart_events',
                use_container_width=False)
