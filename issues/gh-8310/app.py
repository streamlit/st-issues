import streamlit as st
import pandas as pd

st.dataframe(
    {
        "string_list": pd.Series(
            [
                [
                    "Foo Foo Foo Foo Foo Foo Foo Foo Foo Foo Foo Foo Foo Foo Foo Foo Foo Foo Foo Foo Foo Foo",
                    "Bar Bar Bar Bar Bar Bar Bar Bar Bar Bar Bar Bar Bar Bar Bar Bar Bar Bar Bar Bar Bar Bar",
                ]
            ]
        ),
    }
)
