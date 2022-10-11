import streamlit as st

params = st.experimental_get_query_params()
st.write(params)

if st.button("Clean"):
    st.experimental_set_query_params()

if st.button("Set with rerun"):
    st.experimental_set_query_params(**params, q="with_rerun")
    st.experimental_rerun()
