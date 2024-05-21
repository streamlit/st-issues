import streamlit as st

def ask_ai():
  st.write(st.session_state)

st.text_area(
    label="Ask the AI a Question (or ask for a Code Refactor to be done): ",
    key="p_agent_user_input",
)
col1, col2 = st.columns(2)
with col1:
    st.button("Ask AI", on_click=ask_ai)

st.header("In form")
with st.form("agent_form"):
      st.text_area(
          label="Ask the AI a Question (or ask for a Code Refactor to be done): ",
          key="p_agent_user_input_in_form",
      )
      col1, col2 = st.columns(2)
      with col1:
          st.form_submit_button("Ask AI", on_click=ask_ai)
