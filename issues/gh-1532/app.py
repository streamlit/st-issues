import streamlit as st
options = ['zero', 'one', 'two', 'three']
first = st.selectbox('selectbox 1', options, index=2)
second = st.selectbox('selectbox 2', options, index=options.index(first))
