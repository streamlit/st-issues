import streamlit as st

st.header("Issue with widget state in forms")

tab0, tab1 = st.tabs(["Deselect bug", "Select bug"])

with tab0:
    st.write("""
    Repro the issue:
    1. Click the checkbox
    2. Press "Deselect all"

    -> Expected Result: Box is unchecked, output is "False"

    -> Actual Result: The selected box stays checked, but output is "False"
    """)

with tab1:
    st.write("""
    Repro the issue:
    1. Click the "select all" button
    2. Manually deselect the checkbox
    3. Click "select all" again

    -> Expected Result: The box is checked, the output is "True"

    -> Actual Result: The box stays unchecked, but output is "True"
    """)


st.divider()

if "default_val" not in st.session_state:
    st.session_state["default_val"] = False

if st.button("Select All"):
    st.session_state["default_val"] = True
if st.button("Deselect All"):
    st.session_state["default_val"] = False

with st.form(key="data_approval"):
    val = st.checkbox('select', value=st.session_state["default_val"])
    approve_button = st.form_submit_button(label='Do Something')

st.write(f"Value: {val}")
