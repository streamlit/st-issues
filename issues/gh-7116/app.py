import streamlit as st

selection = st.multiselect(label='Multiselect Issue', options=['Cat', 'Mouse', 'Dog'], max_selections=1)
