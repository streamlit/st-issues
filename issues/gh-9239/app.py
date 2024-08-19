import streamlit as st

class Message:
    def __init__(self, type, content):
        self.type = type
        self.content = content

class MessageHistory:
    def __init__(self):
        if "messages" not in st.session_state:
            st.session_state["messages"] = []

    def add_user_message(self, content):
        st.session_state["messages"].append(Message("user", content))

    def add_ai_message(self, content):
        st.session_state["messages"].append(Message("ai", content))

    def add_chat_message(self, role, content):
        st.session_state["messages"].append(Message(role, content))
      
    @property
    def messages(self):
        return st.session_state["messages"]

msgs = MessageHistory()

# Start streamlit app
if len(msgs.messages) == 0:
    intro_message = "Hello! How can I help you?"
    msgs.add_ai_message(intro_message)

for msg in msgs.messages:
    st.chat_message(msg.type).write(msg.content)

if user_input := st.chat_input("Ask a question:"):
    st.chat_message("human").write(user_input.replace("$", "\$"))
    msgs.add_user_message(user_input)

    # Begin AI response code block
    with st.chat_message("ai"):
        with st.spinner("Thinking..."):
          import time

          time.sleep(3)
          # Get AI response (config is needed to pass streamlit session_id)
          response = {"answer": "I am a response from AI"}
          # Fill empty container with AI response
        st.write(response["answer"])
        msgs.add_ai_message(response["answer"])
