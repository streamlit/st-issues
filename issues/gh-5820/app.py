import streamlit as st

st.title('Content inside tabs jitters on first load')

t1, t2, t3 = st.tabs(['First tab','Second tab','Third tab'])

t1.header('This content is inside the first tab')
t2.header('This content is inside the second tab')
t3.header('This content is inside the third tab')
