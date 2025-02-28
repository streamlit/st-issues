import pandas as pd
import streamlit as st

df = pd.DataFrame({"a": [1, 2, 3]})
styler = df.style

st.html(styler.to_html())  # Works as expected
st.dataframe(styler)  # Works as expected
st.table(styler)  # Works as expected

styler.set_tooltips(pd.DataFrame({"a": ["one", "two", "three"]}))

st.html(styler.to_html())  # Works as expected
st.dataframe(styler)  # AttributeError: 'int' object has no attribute 'strip'
st.table(styler)  # AttributeError: 'int' object has no attribute 'strip'
