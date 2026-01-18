import streamlit as st
import pandas as pd


df = pd.DataFrame({
    'copy_these':['a, b, c', 'a b c', 'car, house, horse', 'car house horse'],
    'paste_here': ['', '', '', '']
    })

st.data_editor(df, column_config={'paste_here': st.column_config.SelectboxColumn(
                                    'paste_here',
                                    help='',
                                    width='medium',
                                    options=df['copy_these'].to_list(),
                                    required=False
                                ),})
