import streamlit as st

pop_1 = st.popover("Open")
pop_2 = st.popover("Open")

pop_1.multiselect("Test", options=[i for i in range(3)])
pop_2.multiselect("Test 2", options=[i for i in range(3)])
