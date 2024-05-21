import streamlit as st

def ask_ai():
  print("")

st.text_area(
    label="Ask the AI a Question (or ask for a Code Refactor to be done): ",
    key="p_agent_user_input",
)
col1, col2 = st.columns(2)
with col1:
    st.button("Ask AI", on_click=ask_ai)
