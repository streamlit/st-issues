import altair as alt
import streamlit as st
import pandas as pd
from numpy.random import default_rng

df = pd.DataFrame(default_rng(0).standard_normal((60, 2)), columns=["a", "b"])
base = alt.Chart(df).mark_circle().encode(x="a", y="b").properties(width=400, height=200)
text = base.mark_text(dy=-10).encode(text=alt.Text("b:Q", format=".1f"))

with st.echo():
    st.header('original issue #13410 (VConcat & HConcat)')
    st.caption('With lines 161-168 commented out, it renders exactly the same as is')
    chart = base & (base | base)
    st.altair_chart(chart, width='stretch')

with st.echo():
    # PR #13423 ensures that vega-lite spec defaults to
    # "autosize": {"type": "pad", "contains": "padding"}.
    # The overrun issue persists...
    st.header('My issue (Layered & VConcat) without autosize=fit-x')
    st.caption('As is, the top (layered) chart reverts to 400 width and the bottom chart flows out the container')
    st.caption('With lines 161-168 commented out, it renders but the charts flow out of the container')
    chart = (base + text) & base
    st.altair_chart(chart, width='stretch')

with st.echo():
    # Manually controlling the "autosize" spec produced the desired behavior up
    # until streamlit version 1.52.2 (until PR #13423 was introduced).
    # Commenting out lines 161-168 in
    # `frontend/lib/src/components/elements/ArrowVegaLiteChart/useVegaElementPreprocessor.ts`
    # Fixes this issue when I build `streamlit` on my system runing the React development server
    st.header('My issue (Layered & VConcat) with autosize=fit-x')
    st.caption('As is, the chart does not render')
    st.caption('With lines 161-168 commented out, it produces the desired chart')
    chart = (base + text) & base
    chart = chart.properties(autosize='fit-x')
    st.altair_chart(chart, width='stretch')
