import streamlit as st

with st.chat_message("assistant"):
    st.markdown(
        "<div>Something1 [source](https://google.com)\n\nSomething2 [source](https://google.com)</div>",
        unsafe_allow_html=True
    )


with st.chat_message("assistant"):
    st.markdown(
        "Something1 [source](https://google.com)\n\nSomething2 [source](https://google.com)",
        unsafe_allow_html=True
    )
