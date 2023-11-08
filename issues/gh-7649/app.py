import streamlit as st

st.header("Minimal example.")
selection1=st.selectbox("Select (normal)",["a","b","c"], None, key="select_normal")
st.write(selection1) #writes `None`, as expected.

if "select_keyed" not in st.session_state: st.session_state["select_keyed"] = None
if st.button("reset the keyed"):
  st.session_state["select_keyed"] = None
selection2=st.selectbox("Select (keyed)", ["a","b","c"], key="select_keyed")
st.write(selection2) #writes `None`, as expected, until you interact with any other widget, in which case it will become `a` instead.
st.text_input("You can also type something here and press enter to trigger the bug.")

st.session_state
