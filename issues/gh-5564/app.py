import streamlit as st

st.write(len("🚨"))  # 1
st.write(len("️🚨"))  # 2

st.error("This is an error", icon="🚨") # Works fine
st.error("This is an error", icon="️🚨") # Throws an error
