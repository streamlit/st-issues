import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime
from pandas import DataFrame, bdate_range

alt.renderers.enable('mimetype')

def makeTimeDataFrame(nper=10, freq="B", columns=None, start_date=None):
    if columns is None:
        columns = ["A", "B", "C", "D"]

    if start_date is None:
        start_date = datetime(2000, 1, 1)

    # Create a range of dates
    date_index = bdate_range(start=start_date, periods=nper, freq=freq)

    # For each column, generate nper random numbers
    data = {col: np.random.randn(nper) for col in columns}

    # Build DataFrame
    df = DataFrame(data, index=date_index, columns=columns)
    return df
    
data = makeTimeDataFrame(freq='H')
data = data.reset_index().melt(id_vars="index")

interval = alt.selection_interval(encodings=["x"])

base = (
    alt.Chart(data=data)
    .mark_line(point={"filled": False, "fill": "white"}, strokeWidth=2)
    .encode(
        x=alt.X("index:T", title="Date"),
        y=alt.Y("value", title="Cible"),
    )
)

line_chart = (
    base.encode(
        x=alt.X("index:T", title="Date", scale=alt.Scale(domain=interval.ref())),
        color="variable",
    )
).properties(width=600, height=300)

view = (
    base.add_selection(interval)
    .encode(color="variable")
    .properties(
        width=600,
        height=50,
    )
)

histogram = (
    alt.Chart(data=data)
    .mark_bar().encode(
        alt.X("value:Q", bin=True),
        y=alt.Y("count()"),
    )
).transform_filter(
    interval
)

st.altair_chart(line_chart & view | histogram)
