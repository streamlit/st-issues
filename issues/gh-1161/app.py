import altair as alt
import pandas as pd
import streamlit as st

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
            "formatLocale": {'decimal': ',', 'thousands': '\xa0', 'grouping': [3], 'currency': ['', '\xa0€'], 'percent': '\u202f%'},
            "timeFormatLocale": {'dateTime': '%A %e %B %Y à %X', 'date': '%d/%m/%Y', 'time': '%H:%M:%S', 'periods': ['AM', 'PM'], 'days': ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'], 'shortDays': ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'], 'months': ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'], 'shortMonths': ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']}
        }
    }
)
st.altair_chart(chart)
