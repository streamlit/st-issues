import streamlit as st
import pandas as pd
import numpy as np

df = pd.DataFrame(
   np.random.randn(10, 20),
   columns=('col %d' % i for i in range(20)))

st.dataframe(df.style.highlight_max(axis=0))

st.markdown(df.style.highlight_max(axis=0).to_html(), unsafe_allow_html=True)

st.write("---")

st.dataframe(df.style.highlight_max(axis=0, props='color:darkgrey;background-color:yellow;'))
