import pandas as pd
import altair as alt

df = pd.DataFrame({'a': [1, 2, 3, 4, 5], 'b': [1, 3, 5, 7, 9]})

chart = alt.Chart(df).mark_line().encode(
    x='a',
    y='b'
)

chart

chart_dict = chart.to_dict()
chart2 = alt.Chart.from_dict(chart_dict)

chart2
