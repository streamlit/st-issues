import streamlit as st
import pandas as pd

# max_elements = pd.get_option("styler.render.max_elements")  # default: 262144
# print(max_elements)

# big example with default styler.render.max_elements

# df = pd.DataFrame(list(range(max_elements + 1)))
# This next line always works
# st.dataframe(df)
# Applying formatting fails based on dataframe size. Try commenting out for running smaller example below.
# st.dataframe(df.style.format('{:03d}'))


# small example with small custom styler.render.max_elements
pd.set_option("styler.render.max_elements", 2)

df2 = pd.DataFrame([1, 2, 3])
# This next line always works
st.dataframe(df2)
# Applying formatting fails based on dataframe size
st.dataframe(df2.style.format('{:03d}'))
