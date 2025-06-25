from pathlib import Path

import altair as alt
import pandas as pd
import polars as pl
import streamlit as st

if st.toggle("Use Polars"):
    df = pl.read_parquet(Path("issues") / "gh-11761" / "11761.pq")
else:
    df = pd.read_parquet(Path("issues") / "gh-11761" / "11761.pq")

actual = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x="yearmonth(date):T",
        y="energy_consumption:Q",
        tooltip=["yearmonth(date):T", "energy_consumption:Q"],
        fill="split:N",
    )
)
estimate = (
    alt.Chart(df)
    .mark_line(color="red", point=alt.OverlayMarkDef(filled=True, fill="red"))
    .encode(
        x="yearmonth(date):T",
        y="baseline:Q",
        tooltip=["yearmonth(date):T", "baseline:Q"],
    )
)

chart = actual + estimate
st.altair_chart(chart)
