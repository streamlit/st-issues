import pandas as pd
import streamlit as st

df = pd.DataFrame(
    {
        "ID": [1, 2, 3, 4, 5],
        "IS_ENABLED_REQ": [1, 0, 0, 0, 1],
        "IS_ENABLED_BOOL_REQ": [False, False, False, False, True],
        "IS_ENABLED_REG_DEFAULT": [1, 0, 0, 0, 1],
        "IS_ENABLED_BOOL_REQ_DEFAULT": [False, False, False, False, True],
        "IS_ENABLED_DEFAULT": [1, 0, 0, 0, 1],
        "IS_ENABLED_BOOL_DEFAULT": [False, False, False, False, True],
        "IS_ENABLED": [1, 0, 0, 0, 1],
        "IS_ENABLED_BOOL": [False, False, False, False, True],
    }
)

st.header("DATA_EDITOR_TEST")

grid = st.data_editor(
    data=df,
    column_config={
        "ID": st.column_config.NumberColumn(required=True),
        "IS_ENABLED_REQ": st.column_config.CheckboxColumn(required=True),
        "IS_ENABLED_BOOL_REQ": st.column_config.CheckboxColumn(required=True),
        "IS_ENABLED_REG_DEFAULT": st.column_config.CheckboxColumn(required=True, default=0),
        "IS_ENABLED_BOOL_REQ_DEFAULT": st.column_config.CheckboxColumn(required=True, default=False),
        "IS_ENABLED_DEFAULT": st.column_config.CheckboxColumn(required=False, default=0),
        "IS_ENABLED_BOOL_DEFAULT": st.column_config.CheckboxColumn(required=False, default=False),
        "IS_ENABLED": st.column_config.CheckboxColumn(),
        "IS_ENABLED_BOOL": st.column_config.CheckboxColumn(),
    },
    num_rows="dynamic",
    use_container_width=True,
)
