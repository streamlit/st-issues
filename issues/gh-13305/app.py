import pandas as pd
import streamlit as st

# define df with None values
df = pd.DataFrame({"Number": [None]}, index=[0])

# call data editor
df = st.data_editor(
    data=df,
    column_config={"Number": st.column_config.NumberColumn()},
)

# colun Number is now a list
st.write(df)
