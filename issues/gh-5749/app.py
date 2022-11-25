# ----------------------------------------------------------
# ISSUE 5749

import streamlit as st
import pandas as pd
import plotly.express as px

data = pd.DataFrame((100,120,104,102,203,102),columns=["some_col"])

fig = px.line(data, width=300, height=300)
fig.update_xaxes(visible=False, fixedrange=True)
fig.update_yaxes(visible=False, fixedrange=True)
fig.update_layout(annotations=[], overwrite=True)
fig.update_layout(
  showlegend=False,
  plot_bgcolor="white",
  margin=dict(t=10,l=10,b=10,r=10),
  )

st.header("Issue #5749")
st.subheader("Plotly charts ignore HEIGHT attribute after bug fix PR#5645")
st.write("use_container_width=True, width=300, height=300")
st.caption("**Result: Honors height prop, fills container width**")
st.plotly_chart(fig, config=dict(displayModeBar=False), use_container_width=True)
st.write("use_container_width=False, width=300, height=300")
st.caption("**Result: Ignores height prop & still fills container width**")
st.plotly_chart(fig, config=dict(displayModeBar=False))

# ----------------------------------------------------------
# ISSUE 5761

import streamlit as st
import plotly.express as px

df = px.data.tips()
fig = px.scatter(df, x="total_bill", y="tip", facet_col="sex",
                 width=250, height=200)

fig.update_layout(
    margin=dict(l=20, r=20, t=20, b=20),
    paper_bgcolor="LightSteelBlue",
)

st.header("Issue #5761")
st.subheader("use_container_width parameter of st.plotly_chart stopped working with version 1.14.1")
st.write("use_container_width=True, width=250, height=200")
st.caption("**Result: Honors height prop, fills container width**")
st.plotly_chart(fig, use_container_width=True)
st.write("use_container_width=False, width=250, height=200")
st.caption("**Result: Ignores height prop & still fills container width**")
st.plotly_chart(fig)