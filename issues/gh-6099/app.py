import pandas as pd
import altair as alt

alt.renderers.enable('mimetype')

data = pd._testing.makeTimeDataFrame(freq='H')
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
