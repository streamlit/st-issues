import streamlit as st
import pandas as pd

df = pd.DataFrame(data={'date':[],'value':[]})
editable_df = st.data_editor(
    data=df,
    column_config={
        "date": st.column_config.DateColumn(required=True),
        "value": st.column_config.NumberColumn(default="float"),
    },
    num_rows="dynamic",
    key="clipboard_df",
    use_container_width=True,
    hide_index=False,
)
