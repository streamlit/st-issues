import time

import streamlit as st


def set_state(i: int, text: str):
    st.session_state.stage = i
    st.session_state.lines = text.splitlines()


time.sleep(2)
if "stage" not in st.session_state:
    st.session_state.stage = 0
if st.session_state.stage == 0:
    text = st.text_area("Input your text", height=30)
    st.button(
        "Begin",
        on_click=set_state,
        args=[1, text],
    )
if st.session_state.stage == 1:
    st.title("Your text")
    for i, line in enumerate(st.session_state.lines):
        st.write(f"{i}. {line}")

st.write(st.session_state)

text = st.text_area("Input your text 2", height=30)
st.button(
    "Begin 2"
)
st.write(text)
