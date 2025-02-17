import pandas as pd
import streamlit as st

data_df = pd.DataFrame({"sales": [[0, 100, 200], [-50, 50, 150]]})
st.dataframe(
    data_df,
    column_config={"sales": st.column_config.BarChartColumn("Sales (last 6 months)")},
    hide_index=True,
)
st.dataframe(
    data_df,
    column_config={"sales": st.column_config.AreaChartColumn("Sales (last 6 months)")},
    hide_index=True,
)
st.dataframe(
    data_df,
    column_config={"sales": st.column_config.LineChartColumn("Sales (last 6 months)")},
    hide_index=True,
)
