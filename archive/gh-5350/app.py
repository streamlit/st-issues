import numpy as np
import pandas as pd
import streamlit as st

# Create random dataframe
df = pd.DataFrame(np.random.randn(10, 20), columns=("col %d" % i for i in range(20)))

st.header("This is a header")
st.dataframe(df)

st.markdown("# This is a header")
st.dataframe(df)
