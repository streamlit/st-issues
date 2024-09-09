import streamlit as st
from concurrent.futures import ProcessPoolExecutor

st.title("ProcessPool Test")


def square(x):
    return x * x


def square_multiple(inputs: list) -> list:
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(square, input) for input in inputs]

    return [future.result() for future in futures]


with st.sidebar.form(key="user_inputs"):
    st.session_state["run_button"] = st.form_submit_button(
        label="Run", type="primary", use_container_width=True
    )

st.write(st.session_state["run_button"])

if st.session_state["run_button"] is True:
    values = square_multiple([2, 4, 6])

    st.write(values)

    # Reset the button to false
    st.session_state["run_button"] = False
