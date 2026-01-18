import streamlit as st
from streamlit.components.v1 import html

if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input("streamlit.components.v1 bug")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({"role": "assistant", "content": user_input})

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg["role"] == "assistant":
            html_code = f"""
            <div style="margin-top:5px;">
                <button class="btn btn-sm btn-outline-success" onclick="copyToClipboard('assistant_msg_{i}')">
                    <i class="bi bi-copy"></i> copy
                </button>
                <p id="assistant_msg_{i}" style="display:none;">{msg["content"]}</p>
            </div>

            <script>
                function copyToClipboard(elementId) {{
                    var text = document.getElementById(elementId).innerText;
                    var input = document.createElement('input');
                    input.value = text;
                    document.body.appendChild(input);
                    input.select();
                    input.setSelectionRange(0, 99999);
                    document.execCommand('copy');
                    document.body.removeChild(input);
                }}
            </script>
            """
            html(html_code, height=37.5)
