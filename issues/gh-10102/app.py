import streamlit as st
from time import sleep

sleep(0.2)

def check_on_change(id):
    print(f'on_change {id}')

st.text_input('text')
st.checkbox('check 1', key=f'check_1_input', on_change=check_on_change, args=(1,))
st.checkbox('check 2', key=f'check_2_input', on_change=check_on_change, args=(2,))
st.checkbox('check 3', key=f'check_3_input', on_change=check_on_change, args=(3,))
