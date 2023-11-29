import pandas as pd
import streamlit as st

df = pd.DataFrame(
    {
        "categorical": pd.Series(
            pd.Categorical(
                ["b", "c", "a", "a"], categories=["c", "b", "a"], ordered=True
            )
        ),
        "numbers": pd.Series([1, 2, 3, 4]),
    }
)

st.scatter_chart(df, x="categorical", y="numbers")
