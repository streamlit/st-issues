import streamlit as st

with st.sidebar:
    st.selectbox("Selectbox", ["A", "B", "C"], key="selectbox1")
    st.selectbox("Selectbox", ["A", "B", "C"], key="selectbox2")
    st.selectbox("Selectbox", ["A", "B", "C"], key="selectbox3")
    st.selectbox("Selectbox", ["A", "B", "C"], key="selectbox4")

with st.sidebar.popover("Check 123"):
    st.slider("Slider", key="slider1")
    st.slider("Slider", key="slider2")
    st.slider("Slider", key="slider3")
    st.slider("Slider", key="slider4")
    st.slider("Slider", key="slider5")
