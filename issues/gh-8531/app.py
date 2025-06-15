import streamlit as st
import altair as alt
from vega_datasets import data

def make_plot():
    source = data.barley()

    fig = alt.Chart(source).mark_bar().encode(
        x='year:O',
        y='sum(yield):Q',
        color='year:N',
        column='site:N'
    )
    return fig

fig = make_plot()
# This is okay
st.markdown("This is okay")
st.altair_chart(fig)

# This creates multiple charts instead of one chart
st.markdown("This creates multiple chart, each for a 'site'/column value")
with st.container():
    st.altair_chart(fig, use_container_width=True)
