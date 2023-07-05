import streamlit as st
import pandas as pd

st.title('Guess who?')

st.text_input('First name')
st.text_input('Last name')

st.sidebar.selectbox('Select a demo', ['','A','B'])
