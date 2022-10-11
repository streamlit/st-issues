import streamlit as st

st.write("hello\\ world")
# Displays "hello\ world", as expected

st.write("hello' world")
# Displays "hello' world", as expected

st.write("hello\\' world")
# Displays "hello' world", but "hello\' world" was expected

# To verify my suspicion about double escapes:
st.write("hello\\\\' world")
# Displays "hello\' world", but "hello\\' world" was expected

# This is also broken for other elements
st.info("hello\\' world")
# Displays "hello' world", but "hello\' world" was expected
