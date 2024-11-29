import streamlit as st

st.markdown(":material/info:")  # Works as expected
st.markdown(":material/info:", unsafe_allow_html=True)  # Doesn't work
