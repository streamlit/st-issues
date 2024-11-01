import streamlit as st
import pandas as pd

st.set_page_config(layout='wide')

narrow_dataframe = pd.DataFrame({'narrow_col_1':[1,2,3],'narrow_col_2':[4,5,6],'narrow_col_3':[7,8,9]})
wider_dataframe = pd.DataFrame({'wider_col_1':[1,2,3],'wider_col_2':[4,5,6],'wider_col_3':[7,8,9],'wider_col_4':[10,11,12],'wider_col_5':[13,14,15],'wider_col_6':[16,17,18],'wider_col_7':[19,20,21],'wider_col_8':[22,23,24],'wider_col_9':[25,26,27]})
full_width_dataframe = pd.DataFrame({'full_width_col_1':[1,2,3],'full_width_col_2':[4,5,6],'full_width_col_3':[7,8,9],'full_width_col_4':[10,11,12],'full_width_col_5':[13,14,15],'full_width_col_6':[16,17,18],'full_width_col_7':[19,20,21],'full_width_col_8':[22,23,24],'full_width_col_9':[25,26,27]})

dataframe_selection = st.radio('dataframe selection',['narrow','wider','full width'])
fixed_height = st.checkbox('fixed height',value=False)

if fixed_height:
    narrow_height = 200
    wider_height = 250
    full_width_height = 300
else:
    narrow_height = None
    wider_height = None
    full_width_height = None

if dataframe_selection == 'narrow':
    st.write('narrow dataframe')
    st.dataframe(narrow_dataframe,width=300,height=narrow_height)
    st.write(f'height: {narrow_height}')

elif dataframe_selection == 'wider':
    st.write('wider dataframe')
    st.dataframe(wider_dataframe,width=700,height=wider_height)
    st.write(f'height: {wider_height}')
    
elif dataframe_selection == 'full width':
    st.write('full width dataframe')
    st.dataframe(full_width_dataframe,use_container_width=True,height=full_width_height)
    st.write(f'height: {full_width_height}')
