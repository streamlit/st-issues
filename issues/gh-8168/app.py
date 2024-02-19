import streamlit as st
import pandas as pd

st.title('Bug using links inside dataframe with display_text')
df = pd.DataFrame({'a': [1, 2], 'b': ['http://www.google.com', 'http://www.streamlit.io']})
st.dataframe(df, column_config={"b": st.column_config.LinkColumn(
            "Links",
            help="Open Link",
            width="medium")})
st.dataframe(df, column_config={"b": st.column_config.LinkColumn(
            "Links",
            help="Open Link",
            width="medium",
            display_text="Open link",)})
