import streamlit as st
options = ["a", "b", "c"]
item = st.selectbox("Item", options, index=0, key="item")
st.write("selected", item)
options.pop(0)
st.button("Refresh")
