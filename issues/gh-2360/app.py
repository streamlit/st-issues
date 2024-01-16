import streamlit as st

checked = st.checkbox("I have something")
if checked:
    st.write("Checked")
with st.expander("expand"):
    a = st.selectbox("Choose 1", ['1','2'])
