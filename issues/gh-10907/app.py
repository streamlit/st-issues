import streamlit as st
import time

@st.dialog("Dialog 1")
def show_dialog_1():
    st.write("Dialog 1 content")
    st.text_input("Text input")

@st.dialog("Dialog 2")
def show_dialog_2():
    time.sleep(3)
    st.write("Dialog 2 content")


if st.button("Open dialog 1"):
    show_dialog_1()

if st.button("Open dialog 2"):
    show_dialog_2()
