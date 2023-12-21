import streamlit as st

with st.form(key="async_testing_config"):
        # Components : Select async api endpoints for testing.
        components = st.multiselect(
            "Select async api endpoints",
           ["a", "b", "c"],
            key="components"
        )

        # Submitted - BOOLEAN
        Submitted = st.form_submit_button("Submit")
        if Submitted:
            print("project id: ", project_id)
            print("endpoints: ",components)
