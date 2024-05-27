import streamlit as st
import pandas as pd

index_options = ['A', 'B', 'C']

df = pd.DataFrame({
    'index': ['A', 'B'],
    'value': [1, 2]
})

df.set_index('index', inplace=True)

# Ordinary dataframe, 'index' is in grey
st.dataframe(df)

# Data editor, 'index' is in grey
st.data_editor(df, column_config={
    'index': st.column_config.TextColumn(
        'index',
        required=True,
    ),
    'value': st.column_config.NumberColumn(
        'value',
        min_value=0,
        max_value=10,
        required=True,
    ),
}
)

# Data editor, 'index' is in black
st.data_editor(df, column_config={
    'index': st.column_config.SelectboxColumn(
        'index',
        options=index_options,
        required=True,
    ),
    'value': st.column_config.NumberColumn(
        'value',
        min_value=0,
        max_value=10,
        required=True,
    ),
}
)
