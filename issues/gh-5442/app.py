import streamlit as st

selected_option = st.selectbox("Option", ["A", "B", "C", "D", "E"], key="selection_box")
st.write(f"Selected option: {selected_option }")

if st.button("Reset selection"):
    del st.session_state["selection_box"]
    st.experimental_rerun()
