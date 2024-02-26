import streamlit as st

# it doesn't work
placeholder = st._bottom.empty()
user_input = placeholder.chat_input(placeholder="your first question")
if user_input:
    st.write(f"text input: {user_input}")
    user_input = placeholder.chat_input(placeholder="your second question")

# it works
placeholder = st.sidebar.empty()
user_input = placeholder.chat_input(placeholder="your first question in sidebar")
if user_input:
    st.write(f"text input: {user_input}")
    user_input = placeholder.chat_input(placeholder="your second question in sidebar")
