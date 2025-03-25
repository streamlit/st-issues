import streamlit as st


selection = st.selectbox("My List Box", [ f'Option {i}' for i in range(1,100) ] )
