import pandas as pd
import streamlit as st

data_df = pd.DataFrame(
    {
        "widgets": ["st.selectbox", "st.number_input", "st.text_area", "st.button"],
    }
)

st.dataframe(
    data_df,
    column_config={
        "widgets": st.column_config.Column(
            width="medium"
        )
    }
)
