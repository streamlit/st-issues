import streamlit as st

st.title("Chat Test")
st.write("Try asking something below:")

# Quick options for the user
options = ["What's your name?", "What can you do?", "Tell me something fun",
"Help"]

# Display the pills with a title
selected_pill = st.pills("Quick questions", options, key="selected_pill")

# Show the selected pill
if selected_pill:
    st.write(f"You selected: {selected_pill}")

# Chat input
user_input = st.chat_input("Type your question here")

# Show the input from chat
if user_input:
    st.write(f"You asked: {user_input}")
