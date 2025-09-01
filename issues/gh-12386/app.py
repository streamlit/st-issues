import pandas as pd
import streamlit as st

st.text(st.__version__)

df = pd.DataFrame(
    {
        "id": [1, 2, 3],
        "notes": ["Line 1\nLine 2", "", "A long paragraph...\nSecond line"],
    }
)

edited = st.data_editor(
    df,
    hide_index=True,
    column_config={"notes": st.column_config.TextColumn("Notes", width="large")},
    use_container_width=True,
    key="tbl",
)
