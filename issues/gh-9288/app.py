import streamlit as st

with st.sidebar:
  bn = st.button(
    label = "button with help",
    help = "This is a longer help text to inform users of the functionality and in case it is disabled what to do to enable it. This is a longer help text to inform users of the functionality and in case it is disabled what to do to enable it.",
  )
