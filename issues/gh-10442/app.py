import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# Create a sample dataframe with 3 columns Col1, Col2, Col3
df = pd.DataFrame({
    'Col1': ['A', 'B', 'C'],
    'Col2': ['X', 'Y', 'Z'],
    'Col3': [1, 2, 3]
})

#  Have a dropdown to select a column among Col1, Col2
st.write(f'Poetry Version {st.__version__}')
col = st.selectbox('Select a column', ['Col1', 'Col2'])

# Show the dataframe with the selected column and column Col3
st.dataframe(df, column_order=(col, 'Col3'), use_container_width=True)
