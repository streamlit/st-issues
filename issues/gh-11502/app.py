import streamlit as st

# using fragment breaks sticky positioning of the chat input field


@st.fragment
def simple_chat_test():
    st.title("Simple Chat Test")

    if "test_messages" not in st.session_state:
        st.session_state.test_messages = []
        st.session_state.test_messages.append(
            {
                "role": "assistant",
                "content": "Hi! I'm a simple test bot. I'll respond 'Got it' to everything you say. Try typing something!",
            }
        )

    for message in st.session_state.test_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    with st.expander("Test Content (to make page longer)", expanded=False):
        for i in range(20):
            st.write(f"This is test line {i + 1}")

    if prompt := st.chat_input("Type anything here..."):
        st.session_state.test_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        response = "Got it"
        st.session_state.test_messages.append(
            {"role": "assistant", "content": response}
        )
        with st.chat_message("assistant"):
            st.markdown(response)

        st.rerun()


if __name__ == "__main__":
    simple_chat_test()
