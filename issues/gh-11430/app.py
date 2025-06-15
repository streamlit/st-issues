import streamlit as st

def page_function():
    st.help(st.write)

page = st.navigation([st.Page(page_function)])

st.header("Run the page returned from navigation")
page.run()
st.header("Execute the page function directly")
page_function()
st.header("Directly execute the commands within the page function")
st.help(st.write)
