import streamlit as st

if "apply_workaround" not in st.session_state:
    print("Reloading", flush=True)
    st.session_state["apply_workaround"] = False

st.session_state["apply_workaround"] = st.checkbox("Apply workaround")

st.write(st.session_state)