import streamlit as st
import pandas as pd

data_df = pd.DataFrame(
    {
        "sales": [
            [0,50,100],
            [0,50,200]
        ],
    }
)

st.data_editor(
    data_df,
    column_config={
        "sales": st.column_config.BarChartColumn(
            "Sales (last 6 months)",
            help="The sales volume in the last 6 months",
            y_min=0,
            y_max=100,
        ),
    },
    hide_index=True,
)
