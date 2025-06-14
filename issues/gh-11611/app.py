import streamlit as st

col1, col2 = st.columns(2)

with col1:
  st.selectbox("Selectbox", options=["A", "B"], index=None)
  st.multiselect("Multiselect", options=["A", "B"])
  st.text_input("Text Input", placeholder="Placeholder")
  st.text_area("Text Area", placeholder="Placeholder")
  st.number_input("Number Input", value=None, placeholder="Placeholder")
  st.date_input("Date Input", value=None)
  st.time_input("Time Input", value=None)
  st.chat_input("Chat Input")

with col2:
  st.selectbox("Selectbox (disabled)", options=["A", "B"], index=None, disabled=True)
  st.multiselect("Multiselect (disabled)", options=["A", "B"], disabled=True)
  st.text_input("Text Input (disabled)", placeholder="Placeholder", disabled=True)
  st.text_area("Text Area (disabled)", placeholder="Placeholder", disabled=True)
  st.text_area("Number Input (disabled)", value=None, placeholder="Placeholder", disabled=True)
  st.date_input("Date Input (disabled)", value=None, disabled=True)
  st.time_input("Time Input (disabled)", value=None, disabled=True)
  st.chat_input("Chat Input (disabled)", disabled=True)
