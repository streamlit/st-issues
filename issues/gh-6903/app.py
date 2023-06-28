import streamlit as st
import pandas as pd
import altair as alt
alt.data_transformers.disable_max_rows()

def getEnsemblePlotData(plotDf: pd.DataFrame) -> list[pd.DataFrame]:
    plotDf = plotDf.set_index(['forecastDate','times']).stack()
    plotDf.index.names = ['forecastDate','times', 'member']
    plotDf.name = 'flow'
    plotDf = plotDf.reset_index()

    det = plotDf.loc[plotDf.member == 'FOLC1F', :]
    ens = plotDf.loc[plotDf.member != 'FOLC1F', :]
    return det, ens

df = pd.read_json('https://raw.githubusercontent.com/danhamill/hindcastDataAssessment/master/data/streamlit_issue.json')
df.loc[:,'times'] = pd.date_range('1986-02-01 04:00:00', '1986-02-16 04:00:00', freq='H')

det, ens = getEnsemblePlotData(df)


detChart = alt.Chart(det).mark_line(color='black').encode(
x=alt.X("times\:T").axis(title="Time (PST)"),
y=alt.Y("flow\:Q").axis(title="Flow (CFS)")
)

selection = alt.selection_point(fields = ["member"], bind="legend")
domain = [str(i) for i in range(1980,2021)]
range_ = ['grey']*41
ensChart = alt.Chart(ens).mark_line( strokeWidth=0.5).encode(
    x=alt.X("times\:T").axis(title="Time (PST)"),
    y=alt.Y("flow\:Q").axis(title="Flow (CFS)"),
    color = alt.Color("member").legend(columns=2, symbolLimit=41).scale(domain=domain, range = range_),
    opacity= alt.condition(selection, alt.value(1), alt.value(0.2))
).add_params(
    selection
)

chart = alt.layer(ensChart, detChart)

st.altair_chart(chart)
