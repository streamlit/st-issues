import streamlit as st

with st.expander("expander:"):
    value = st.number_input("number", value=1.0, key="vl_key")
    # insert a values

st.write(st.session_state["vl_key"])


def update_value():
    st.session_state["vl_key"] = 0.0


update_button = st.button("Update", on_click=update_value)

st.write(st.session_state["vl_key"])

print_value = st.button("Print value")
if print_value:
    st.write(st.session_state["vl_key"])
