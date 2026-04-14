import pandas as pd
import streamlit as st

data_df = pd.DataFrame([["https://roadmap.streamlit.app", "https://extras.streamlit.app", "https://issues.streamlit.app"]])

st.dataframe(
    data_df.style,
    width="content",
    column_config={
        "0": st.column_config.LinkColumn("22px", width=22, display_text="🔗"),
        "1": st.column_config.LinkColumn("44px", width=44, display_text=":material/open_in_new:"),
        "2": st.column_config.LinkColumn("43px", width=43, display_text=":material/open_in_new:"),
    },
)
