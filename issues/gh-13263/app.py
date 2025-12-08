import streamlit as st

@st.dialog('Dialog')
def open_dialog():
    st.segmented_control('Widget',options=range(5))

if st.button('Open Dialog', shortcut='D'):
    open_dialog()

if st.button('Open Dialog with Shift', shortcut='Shift+D'):
    open_dialog()

if st.button('Open Dialog with Ctrl', shortcut='Ctrl+D'):
    open_dialog()
