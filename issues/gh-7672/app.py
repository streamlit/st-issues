#Using the code example from streamlit doc column_config with values changed
import pandas as pd
import streamlit as st

data_df = pd.DataFrame(
    {
        "sales": [
            [9, 4, 26, 80, 100, 40],
            [80, 20, 80, 35, 40, 100],
            [21, 20, 80, 80, 70, 0],
            [100, 100, 20, 100, 30, 100],
        ],
    }
)

st.dataframe(
    data_df,
    column_config={
        "sales": st.column_config.LineChartColumn(
            "Sales (last 6 months)",
            width="medium",
            help="The sales volume in the last 6 months",
            y_min=0,
            y_max=100,
         ),
    },
    hide_index=True,
)
