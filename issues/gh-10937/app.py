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
