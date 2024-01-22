import streamlit as st

age = st.slider('How old are you?', min_value=1, max_value=10, value=12)
st.write("I'm ", age, 'years old')

age = st.number_input('How old are you?', min_value=1, max_value=10, value=12)
st.write("I'm ", age, 'years old')
