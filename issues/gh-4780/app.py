import streamlit
import altair

chart = altair.Chart().mark_text(text="FFS", size=160).encode(x=altair.value(0), y=altair.value(0))
figure = streamlit.altair_chart(chart)
