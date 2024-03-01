import streamlit as st
# Contains data of more than two data types
mixedData = {'mixed': ['10', 20, 30]}
# Contains data of single data types
singleData = {'single': [10, 20, 30]}
# create 
st.data_editor(pd.DataFrame(mixedData), disabled=False)
st.data_editor(pd.DataFrame(singleData))
