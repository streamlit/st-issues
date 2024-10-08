import streamlit as st

def callback():
    call = st.session_state.test_balloons
    if call:
        print("AAAAAAAAAAA") ## this gets printed
        st.balloons()  ## NO BALLOONS

@st.fragment   ## if I comment out st.fragment, it works
def test():
    button = st.toggle("turn on balloons", on_change=callback, value=True, key="test_balloons")
    # if button: <- These lines work if I uncomment them
    #     st.balloons()

test()
