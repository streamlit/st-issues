import streamlit as st

c1, c2 = st.columns([2, 5])
c1.markdown('Username: :red[*]')

params = {}
params.setdefault('label_visibility', 'collapsed')
c2.text_input('', **params)
