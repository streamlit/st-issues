import streamlit as st

@st.fragment(run_every=0.2)
def func2():
    st.button("OK2")

@st.fragment(run_every=0.5)
def func():
    st.button("OK")
    func2()

func()
