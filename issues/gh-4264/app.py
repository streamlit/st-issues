import streamlit as st
options_1 = ["Alice", "Bob"]
options_2 = ["Amy", "Barry"]

if st.checkbox("Swap names"):
    options = options_1
else:
    options = options_2

st.write("Choose between {} and {} by first letter".format(*options))

name = st.selectbox("First letter", options, format_func=lambda x: x[0])

st.write(f"You chose {name}")
