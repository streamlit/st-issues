import string
import pandas as pd
import streamlit as st

st.session_state.counter = 0
st.title("Minimal Working Example")


@st.fragment(run_every=0.5)
def fragment():
    st.session_state.counter += 1
    st.write(f"Counter: {st.session_state.counter}")

@st.fragment(run_every=0.5)
def fragment_two():
    st.write("This is a fragment that runs every 0.5 seconds.")

if st.toggle("Run Fragment", value=True):
    fragment()

if st.toggle("Run Fragment Two", value=True):
    fragment_two()

data = pd.DataFrame({"column_1": ["b"]})
st.data_editor(
    data,
    hide_index=True,
    column_config={
        "column_1": st.column_config.SelectboxColumn(
            "Select", options=list(string.ascii_lowercase)
        )
    },
)

st.selectbox(
    "Select",
    options=list(string.ascii_lowercase),
    key="selectbox",
    help="This is a selectbox",
)
