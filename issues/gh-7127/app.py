import streamlit as st  

options = ['Option 1', 'Option 2']  
selected_option = st.radio('Select an option', options, help='Select one of the options', horizontal=True, label_visibility='hidden')  

st.write('You selected ', selected_option)
