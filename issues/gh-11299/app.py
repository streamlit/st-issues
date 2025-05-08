import numpy as np
import pandas as pd

import streamlit as st

np.random.seed(42)
# Create a random dataframe with 50k rows:

df = pd.DataFrame(
    {
        "col1": np.random.randint(0, 100, size=50000),
        "col2": np.random.randint(0, 100, size=50000),
    }
)

rows_to_show = st.slider("Rows to show", min_value=10, max_value=100, value=20, step=10)

# time.sleep(1)
st.dataframe(df, height=40 + (rows_to_show * 30))  # <- yes a little math voodoo
st.dataframe(df)  # <- yes a little math voodoo
if st.button("Rerun"):
    st.rerun()
