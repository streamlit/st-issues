import streamlit as st

words = ["a", "b", "c"]

# Without space after colon, the first word is replaced with a newline character
st.write("Words:", ','.join(words))
st.info("Words:" + ', '.join(words))

# With space after colon it works
st.write("Words: ", ','.join(words))
st.info("Words: " + ', '.join(words))

st.info("Words:a, b, c")
