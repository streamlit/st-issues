import streamlit as st
c1, c2, c3 = st.columns([1, 1, 1])

with c1:
    st.button('button 1', use_container_width=True)
with c2:
    st.button('button 2', use_container_width=True)
with c3:
    st.button('button 3', use_container_width=True, help = 'example')
st.button("test", use_container_width=True, help='test')
