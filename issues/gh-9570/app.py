import pandas as pd
import streamlit as st

st.write('Table 1 (no index)')
df_no_index = pd.DataFrame(
    data={'A': [1, 2, 3], 'B': [11, 12, 13]}
)
st.data_editor(df_no_index)

st.write('Table 2 (number index)')
df_number_index = pd.DataFrame(
    data={'A': [1, 2, 3], 'B': [11, 12, 13]},
    index=[0, 1, 2],
)
st.data_editor(df_number_index)

st.write('Table 3 (string index)')
df_string_index = pd.DataFrame(
    data={'A': [1, 2, 3], 'B': [11, 12, 13]},
    index=['a', 'b', 'c'],
)
st.data_editor(df_string_index)
