import streamlit as st
import pandas as pd

df = pd.DataFrame([["/test?param=KO", "/test?param=OK&demo=1"]], columns=["col1", "col2"])
            st.data_editor(
                data=df,
                column_config={
                    "col1": st.column_config.LinkColumn(display_text="/test\?param=(.*?)"),
                    "col2": st.column_config.LinkColumn(display_text="/test\?param=(.*?)&demo=1")
                })
