import streamlit as st

st.title("With center tag")
st.markdown("""<center> Hello `World!`</center>""", unsafe_allow_html=True)

st.title("Without center tag")
st.markdown("""Hello `World!`""")
