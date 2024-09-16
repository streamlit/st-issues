import streamlit as st
import pandas as pd
import altair as alt


st.title("Altair Chart cut-off bug")


df = pd.DataFrame(
    {"x": [1, 2, 3, 4], "y": [1, 2, 3, 4], "category": ["A", "B", "C", "D"]}
)

chart = (
    alt.Chart(df)
    .mark_line(point=True)
    .encode(
        x=alt.X("x", title="Date"),
        y=alt.Y("y:Q", title="Legend Value"),
        color=alt.Color("category:N", title="Category").legend(
            orient="bottom", title=None
        ),
    )
)

st.write("use_container_width=True")
st.altair_chart(chart, use_container_width=True)

# THE REST OF THIS JUST SHOWS MORE EXAMPLES

st.write("use_container_width=False")
st.altair_chart(chart, use_container_width=False)

st.write("No bottom legend")
# This one renders properly initially
chart = (
    alt.Chart(df)
    .mark_line(point=True)
    .encode(
        x=alt.X("x", title="Date"),
        y=alt.Y("y:Q", title="Legend Value"),
        color=alt.Color("category:N", title="Category"),
    )
)

st.altair_chart(chart, use_container_width=True)


st.button("Rerender")
