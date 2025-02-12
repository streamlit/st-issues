import streamlit as st
import pandas as pd

test_df = pd.DataFrame({
    'Date': pd.date_range(start='2024-01-01', periods=10),
    'Value1': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
    'Value2': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
    'Value3': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
    'Value4': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
    'Value5': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
    'Value6': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
    'Value7': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
    'Value8': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
})

col_config = {
    'Date': st.column_config.DateColumn(width="medium",pinned=True),
    'Value1': st.column_config.NumberColumn('Value1 Pinned', width="medium", format='%.2f',pinned=True),
    'Value2': st.column_config.NumberColumn(width="medium", format='%.2f',pinned=False),
    'Value3': st.column_config.NumberColumn(width="medium", format='%.2f',pinned=False),
    'Value4': st.column_config.NumberColumn(width="medium", format='%.2f',pinned=False),
    'Value5': st.column_config.NumberColumn(width="medium", format='%.2f',pinned=False),
    'Value6': st.column_config.NumberColumn(width="medium", format='%.2f',pinned=False),
    'Value7': st.column_config.NumberColumn(width="medium", format='%.2f',pinned=False),
    'Value8': st.column_config.NumberColumn(width="medium", format='%.2f',pinned=False)
}

st.write('hide index = True')
st.dataframe(test_df, column_config=col_config, hide_index=True)

st.write('hide index = False')
st.dataframe(test_df, column_config=col_config, hide_index=False)
