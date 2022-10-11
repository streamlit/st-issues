from time import sleep

import streamlit as st

with st.form("input"):
    selected_options = st.sidebar.multiselect(
        "Select options for left column:",
        ["Option1", "Option2", "Option3"],
        default="Option1",
    )
    submit_button = st.form_submit_button(label="Extract data")

if submit_button:
    with st.spinner(text="Extracting information..."):
        sleep(0.1)
        st.write("You selected: {}".format(selected_options))
