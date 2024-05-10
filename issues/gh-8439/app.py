import streamlit as st

cols = st.columns(2)

cols[0].text("I'm a column!")
cols[0].number_input('My help hover does not work', help='test')
cols[0].number_input('My help hover works', help='test')
cols[1].header('Hello World!', anchor=False)
