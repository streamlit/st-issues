import streamlit as st

state = st.selectbox("State", ["California", "New York", "Washington"])

if state == "California":
    cities = ["Los Angeles", "San Francisco", "San Diego"]
elif state == "New York":
    cities = ["New York", "Buffalo"]
elif state == "Washington":
    cities = ["Seattle", "Olympia"]

index, city = st.selectbox("City", enumerate(cities), format_func=lambda index_and_city: index_and_city[0])

st.markdown("City: **%s**, State: **%s**" % (city, state))
