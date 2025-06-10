import altair as alt
import pandas as pd
import streamlit as st
from vega_datasets import data

source = data.seattle_weather()

with st.sidebar:
    data_toggle = st.toggle("Data")

if data_toggle:
    data_list = ["date", "temp_max", "precipitation"]
else:
    data_list = ["date", "temp_min", "temp_max", "wind", "precipitation"]

data = pd.melt(
    source[data_list], id_vars=["date"], var_name="signal", value_name="Value"
)

_base = alt.Chart(data).encode(
    x=alt.X(
        "date:T",
        axis=alt.Axis(
            title=None,
            format="%d-%b-%Y",
            labelAngle=25,
            labelBound=True,
            labelAlign="left",
        ),
    ),
)

_area = _base.mark_line().encode(
    y=alt.Y("Value:Q"),
    color="signal:N",
)

_hline = (
    alt.Chart(pd.DataFrame({"y": [20]}))
    .mark_rule(color="red", strokeDash=[5, 5])
    .encode(y="y")
)

with st.sidebar:
    on = st.toggle("Line?")

if on:
    chart = alt.layer(_hline, _area)
else:
    chart = alt.layer(_area)

tab1, tab2 = st.tabs(["Streamlit theme (default)", "Altair native theme"])
with tab1:
    st.altair_chart(chart, theme="streamlit", use_container_width=True)
with tab2:
    st.altair_chart(chart, theme=None, use_container_width=True)
