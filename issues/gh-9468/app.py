import streamlit as st

# Extract the environment from the query parameter
query_params = st.query_params
selected_hours = int(query_params.get_all("hours", [24])[0]) 
selected_bus_name = query_params.get_all("buses", ["MP"])
st.query_params.hours = int(selected_hours)
st.query_params.buses = selected_bus_name

num_hours = st.sidebar.slider("Select Number of Hours", min_value=1, max_value=72, value=selected_hours)
bus_names = st.sidebar.multiselect("Select Event Buses", ["MP", "UP", "Maha", "Hary", "Telum"],
                                  default=selected_bus_name)
st.query_params.hours = int(num_hours)
st.query_params.buses = bus_names

# Display the selected hours
st.write(f"Selected Hours: {num_hours}")
st.write(f"Selected Bus : {bus_names}")
