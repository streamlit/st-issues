import altair as alt
from vega_datasets import data

states = alt.topo_feature(data.us_10m.url, 'states')
pop = data.population_engineers_hurricanes()

chart = alt.Chart(states).mark_geoshape().encode(
	color='population:Q'
).transform_lookup(
	lookup='id',
	from_=alt.LookupData(pop, 'id', list(pop.columns))
).properties(
	width=500,
	height=300
).project(
	type='albersUsa'
)

st.altair_chart(chart)
