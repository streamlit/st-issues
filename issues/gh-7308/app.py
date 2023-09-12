import streamlit as st
from random import random

random_str = str(random())
print(random_str)

clicked = st.download_button(
    label='Download some text', 
    data=random_str
)
st.write(clicked)
print(clicked)
