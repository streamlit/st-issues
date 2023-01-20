# %%
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

# %%
df = pd.DataFrame(
    {
        "index_x": [1, 2, 3, 1, 2, 3, 1, 2, 3],
        "index_y": [1, 1, 1, 2, 2, 2, 3, 3, 3],
        "value": np.random.rand(9),
    }
)

# %%
# df

# %%
ordering = [2, 3, 1]

# %%
ch = (
    alt.Chart(df)
    .mark_rect()
    .encode(
        x=alt.X("index_x:O", sort=ordering),
        y=alt.Y("index_y:O", sort=ordering),
        color="value:Q",
        tooltip=[
            "index_x",
            "index_y",
            "value",
        ],
    )
)

# %%
# ch

# %%
st.altair_chart(ch)  # , use_container_width=True)
