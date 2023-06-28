import streamlit as st


def expanded():
    st.session_state["expanded"] = False


with st.expander("Expander", st.session_state.get("expanded", True)):
    st.text(f"{st.session_state.get('expanded', True) = }")
    st.button("Fold", on_click=expanded)
