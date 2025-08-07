import streamlit as st

st.session_state["disable"] = st.session_state.get("disable", False)
st.session_state["counter"] = st.session_state.get("counter", 0) + 1

counter = st.session_state["counter"]
st.info(f"Script rerun {counter} times")

files = st.file_uploader(label = "", disabled = st.session_state["disable"])

st.info(f"File uploaded: {files is not None}")

button = st.button("Enable" if st.session_state["disable"] else "Disable")
if button:
    st.session_state["disable"] = not st.session_state["disable"]
    st.rerun()
