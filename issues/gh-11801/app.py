import streamlit as st
import pandas as pd

# Example DataFrame
df = pd.DataFrame({
    "A": [1, 2, 3],
    "B": ["x", "y", "z"],
    "C": [True, False, True],
})

# Display DataFrame with column "B" hidden
st.dataframe(
    df,
    hide_index=True,  # optional: hide the row index
    column_config={
        "B": None      # hide column "B"
    }
)
