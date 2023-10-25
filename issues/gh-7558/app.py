import pandas as pd
import streamlit as st

data_df = pd.DataFrame(
    {
        "price": [1, 2, 3, 4],
    }
)
import math
st.data_editor(
    data_df,
    column_config={
        "price": st.column_config.SelectboxColumn(
            "Price (in USD)",
            help="The price of the product in USD",
            disabled=True,
            options=[1,2,3,4,float('nan')]
        )
    },
    hide_index=True,
)
