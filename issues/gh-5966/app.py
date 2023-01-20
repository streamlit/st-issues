import altair as alt
import numpy as np
import pandas as pd

import streamlit as st

st.sidebar.title("Sidebar")
st.sidebar.markdown("This is the sidebar")

df = pd.DataFrame({"first column": [1, 2, 3, 4], "second column": [10, 20, 30, 40]})

use_container_width = st.checkbox("Use container width", value=False)

with st.expander("See raw data", expanded=True):
    st.dataframe(df, use_container_width=use_container_width)
    st.altair_chart(
        alt.Chart(df).mark_bar().encode(x="first column", y="second column"),
        use_container_width=use_container_width,
    )
