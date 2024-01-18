import streamlit as st

if st.button("run with spinner"):
    with st.spinner("please wait"):
        pass

st.button("run without spinner")

tab1, tab2 = st.tabs(["tab1", "tab2"])
tab1.write('tab1')
tab2.write('tab2')
