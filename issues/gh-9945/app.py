import streamlit as st

st.markdown(":material/info: :red[red text]")  # Works as expected
st.markdown(":material/info: :red[red text]", unsafe_allow_html=True)  # Doesn't work
