import pandas as pd
import streamlit as st


def set_state(i: int, df: pd.DataFrame) -> None:
    st.session_state.stage = i
    st.session_state.df = df


if "stage" not in st.session_state:
    st.session_state.stage = 0

if st.session_state.stage == 0:
    st.write("Input your data")
    df = st.data_editor(pd.DataFrame({"col1": ["a", "b"], "col2": ["c", "d"]}))
    st.button(
        "Begin",
        on_click=set_state,
        args=[1, df],
    )

if st.session_state.stage == 1:
    st.write("Your data")
    st.dataframe(st.session_state.df)
