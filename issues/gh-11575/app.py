import pandas as pd
import streamlit as st

df = pd.DataFrame(
    {
        "A": ["foo", "foo", "foo", "bar", "bar", "bar", "baz", "baz", "baz"],
        "B": ["one", "one", "two", "two", "one", "one", "two", "two", "one"],
    }
)
st.dataframe(df)
