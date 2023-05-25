import streamlit as st
import pandas as pd

df = pd.DataFrame(columns=['Name', 'Age', 'Amt'])

edited_df = st.experimental_data_editor(df, num_rows='dynamic', key="data_editor_1")
st.caption("This is working fine with pandas >= 2, but not with older versions")

st.subheader("Fixed version:")

df = pd.DataFrame(columns=['Name', 'Age', 'Amt'], index=pd.RangeIndex(start=0, step=1))
edited_df = st.experimental_data_editor(df, num_rows='dynamic', key="data_editor_2")
