import streamlit as st

app_modes = {
	"run_app": "Run the app",
  "show_docs": "Show the docs",
}

# select the app mode
app_mode = st.selectbox("App mode", app_modes)
