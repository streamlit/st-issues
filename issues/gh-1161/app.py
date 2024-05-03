import altair as alt
import pandas as pd
import streamlit as st
import vl_convert as vlc

df = pd.DataFrame({
    'date': pd.date_range('2020-01-01', freq='M', periods=6),
    'revenue': [100000, 110000, 90000, 120000, 85000, 115000]
})

chart = alt.Chart(df).mark_bar().encode(
    y='month(date):O',
    x=alt.X('revenue:Q', axis=alt.Axis(format='$,r'))
).properties(
    usermeta={
        "embedOptions": {
            "formatLocale": vlc.get_format_locale("fr-FR"),
            "timeFormatLocale": vlc.get_time_format_locale("fr-FR")
        }
    }
)
st.altair_chart(chart)
