import streamlit as st 

with st.echo():
    st.markdown(":gray[This is st.markdown gray]")
with st.echo():
    st.caption("This is st.caption gray")
with st.echo():
    st.caption("**This is st.caption bold gray**")
