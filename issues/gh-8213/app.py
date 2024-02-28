import streamlit as st

cols = st.columns(5)
cols[0].multiselect("Multiselect", ["A long option"], default="A long option")
