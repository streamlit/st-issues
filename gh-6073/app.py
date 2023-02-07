import pandas as pd
import streamlit as st


df = pd.DataFrame({'a': [1, 2], 'b': [11, 22]})

print('okay with full df')
st.dataframe(df)

print('add a new column')
df['value'] = [[1, 1.1], 2]
print('problem with a small portion of df that includes the new column')
st.dataframe(df[['a', 'value']])

print('no problem with the new full df')
st.dataframe(df)

if st.button('rerun'):
    print('---try experiment again---')
    st.experimental_rerun()
