import streamlit as st

st.title("Scrolling issue")

for _ in range(50):
    st.text("")

st.markdown("####")
st.markdown("#### You did not see it, but the browser scrolled down")
st.markdown(
    "There is an issue in Streamlit that allows you to trick the browser to scroll down to a particular element.",
)
st.markdown(
    (
        'If you render a `st.markdown("####")`, the browser will render it as `<h4 id />`'
        "and because the id is empty, the browser scrolls to it"
    ),
)
