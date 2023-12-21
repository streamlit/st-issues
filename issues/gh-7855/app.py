import streamlit as st
import random 

with st.form(key="async_testing_config"):
        # Components : Select async api endpoints for testing.
        components = st.multiselect(
            "Select async api endpoints",
           random.choices(["a", "b", "c", "d", "e"], k=4),
            key="components"
        )

        # Submitted - BOOLEAN
        Submitted = st.form_submit_button("Submit")
        if Submitted:
            st.write("endpoints: ",components)
