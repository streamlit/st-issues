import streamlit as st
with st.expander("Weight Loss", expanded=True):
    weight_goal = 200
    initial_weight = 275.0
    todays_weight = st.number_input("Current Weight", value=initial_weight, min_value=170.0, max_value=280.0, step=0.2, help ="Goal is 200.")


