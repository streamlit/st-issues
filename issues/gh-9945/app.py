import streamlit as st

st.markdown(":material/info: :red[red text] :streamlit:")  # Works as expected
st.markdown(":material/info: :red[red text] :streamlit:", unsafe_allow_html=True)  # Doesn't work
