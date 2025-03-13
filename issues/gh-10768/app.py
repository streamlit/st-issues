import pandas as pd
import streamlit as st

df = pd.DataFrame({"solid": [0.1, 0.2, 0.3], "gradient": [0.4, 0.5, 0.6], "bar": [0.7, 0.8, 0.9]})
styler = df.style
styler.format(lambda x: f"{x:.0%}")
styler.map(lambda x: f"background-color: green;", subset="solid")
styler.map(lambda x: f"background: linear-gradient(to right, green {x:%}, transparent {x:%});", subset="gradient")
styler.bar(subset="bar", vmin=0, vmax=1, color="green")  # Uses a `background: linear-gradient` under the hood.

st.code("st.table()")
st.table(styler)  # Both the solid color and the gradient work as expected.
st.divider()
st.code("st.dataframe()")
st.dataframe(styler)  # The solid color works as expected, but not the gradient.
