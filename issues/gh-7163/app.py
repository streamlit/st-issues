import streamlit as st

with st.expander("Weight Loss", expanded=True):
    weight_goal = 200
    initial_weight = 275.0
    todays_weight = col1.number_input("Current Weight", value=initial_weight, min_value=170.0, max_value=280.0, step=0.2, help="Goal is 200.")

# Convert the float to a formatted string without trailing zeros
formatted_weight = f"{todays_weight:.1f}"  # Display up to 1 decimal place

st.write("Formatted Weight:", formatted_weight)
