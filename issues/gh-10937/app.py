import numpy as np
import pandas as pd

import streamlit as st

is_transposed = st.checkbox("Transpose", value=False)

df = pd.DataFrame(
    {
        "foo": ["one", "one", "one", "two", "two", "two"],
        "bar": ["A", "B", "C", "A", "B", "C"],
        "baz": [1, 2, 3, 4, 5, 6],
        "zoo": ["x", "y", "z", "q", "w", "t"],
    }
)

st.dataframe(df.T if is_transposed else df)
st.dataframe(df.T)

with st.form("Generate random dataframe"):
    num_rows = st.number_input("Number of rows", value=6, min_value=1, max_value=100)
    num_cols = st.number_input("Number of columns", value=5, min_value=1, max_value=100)
    prefix = st.text_input("Prefix", value="col_")
    st.form_submit_button("Generate")

df = pd.DataFrame(
    np.random.randn(num_rows, num_cols),
    columns=(prefix + str(i) for i in range(num_cols)),
)

st.dataframe(df)
