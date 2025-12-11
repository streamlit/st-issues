import streamlit as st

cols = st.columns(2)
with cols[0]:
    st.button("Button 1", width="stretch")
    st.button("Button 2", width="stretch")
with cols[1]:
    with st.container(horizontal=True):
        st.checkbox("Checkbox 1")
        st.checkbox("Checkbox 2")
        st.checkbox("Checkbox 3")
    with st.container(horizontal=True):
        st.checkbox("Checkbox 4")
        st.checkbox("Checkbox 5")
        st.checkbox("Checkbox 6")
