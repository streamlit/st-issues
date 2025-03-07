import streamlit as st
import pandas as pd

samples = {
    "col1": ["test11", "test12", "test13"],
    "col2": ["test21", "", "test23"],
    "col3": ["test31", "test32", None]
}

df = pd.DataFrame(samples)
editor = st.data_editor(df, num_rows="dynamic")
