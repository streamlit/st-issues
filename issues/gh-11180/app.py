import streamlit as st
import pandas as pd

df2 = pd.DataFrame([
    {"ID": 1, "NAME": "Guillaume"},
    {"ID": 2, "NAME": "Tim"},
    {"ID": 3, "NAME": "me"},
    {"ID": 4, "NAME": "aname2"},
    {"ID": 5, "NAME": "aname"}
])
df2["NAME"] = df2["NAME"].astype("string")


with st.form(key="edit_table2"):
    new_df2 = st.data_editor(df2, num_rows="dynamic", key="new_df2")
    submitted = st.form_submit_button("Submit2")

st.write(new_df2)
