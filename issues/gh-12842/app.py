import pandas as pd
import streamlit as st

data_df = pd.DataFrame(
    columns=[
        "category", "test"
    ]
)
edited_data = st.data_editor(
    data_df,
    num_rows="dynamic",
    column_config={
        "test": st.column_config.TextColumn('test'),
        "category": st.column_config.MultiselectColumn(
            "App Categories",
            help="The categories of the app",
            options=[
                "exploration",
                "visualization",
                "llm",
            ],
        ),
    },
)
st.write(edited_data)
