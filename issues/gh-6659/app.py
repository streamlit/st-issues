import streamlit as st
import pandas as pd

df = pd.DataFrame({'A':[1,2,3],'B':[1,2,3]})

cols = st.columns(3)
df = df.reset_index()
cols[0].write('Dataframe display')
cols[0].dataframe(df)
cols[1].write('Data Editor display')
cols[1].experimental_data_editor(df, num_rows='dynamic')
cols[2].write('Column Types')
cols[2].write(df.dtypes)

cols = st.columns(3)
df.index = ['a','b','c']
cols[0].write('Dataframe display')
cols[0].dataframe(df)
cols[1].write('Data Editor display')
cols[1].experimental_data_editor(df, num_rows='dynamic')
cols[2].write('Column Types')
cols[2].write(df.dtypes)

cols = st.columns(3)
df = df.reset_index()
cols[0].write('Dataframe display')
cols[0].dataframe(df)
cols[1].write('Data Editor display')
cols[1].experimental_data_editor(df, num_rows='dynamic')
cols[2].write('Column Types')
cols[2].write(df.dtypes)
