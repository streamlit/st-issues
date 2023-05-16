import streamlit as st

df1 = [[3],[2],2,'asd','a']
df2 = [[3],[2],'2','asd','a']
df3 = ['2',[3],[2],'asd','a']
df4 = [2,[3],[2],'asd','a']
df5 = ['asd',[3],[2],2,'a']
df6 = ['asd',[3],'a',[2],'a']
df7 = ['asd',[3],'a',[2],2]

data = [df1,df2,df3,df4,df5,df6,df7]

st.write(st.__version__)

if st.__version__.startswith('1.22'):
    for i,df in enumerate(data):
        cols = st.columns(2)
        cols[0].write(f'df{i+1}')
        cols[0].write(repr(df))
        try:
            cols[1].experimental_data_editor(df)
        except Exception as e:
            cols[1].write(e)
else:
    for i,df in enumerate(data):
        cols = st.columns(2)
        cols[0].write(f'df{i+1}')
        cols[0].write(repr(df))
        try:
            cols[1].dataframe(df)
        except Exception as e:
            cols[1].write(e)
