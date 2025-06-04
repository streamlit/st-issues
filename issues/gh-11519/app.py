import streamlit as st
import pandas as pd

df = pd.DataFrame({"min_diameter": [4.51]})
result_df = st.data_editor(
    df,
    column_config={
        "min_diameter": st.column_config.NumberColumn(
            "MIN DM",
            min_value=0.00,
            # step=0.01,
            format="%.2f",
            width="small",
        )
    },
    num_rows="dynamic",
    use_container_width=True,
)
st.dataframe(result_df)
