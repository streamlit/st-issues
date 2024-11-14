from datetime import time, timedelta
import pandas as pd
import streamlit as st

data_df = pd.DataFrame(
    {
        "appointment": [
            time(12, 0),
            time(18, 15),
            time(9, 30),
            time(16, 45),
        ]
    }
)

st.data_editor(
    data_df,
    column_config={
        "appointment": st.column_config.TimeColumn(
            "Appointment",
            min_value=time(8, 0, 0),
            max_value=time(19, 0, 0),
            format="hh:mm A",
            step=timedelta(minutes=15),
        ),
    },
    hide_index=True,
    num_rows="dynamic",
)
