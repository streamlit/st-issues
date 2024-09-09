import streamlit as st

radio_value = st.radio("Select1", ["Egg", "Spam", "Bacon", "Sausage"])
st.write(radio_value)

if st.button("Rerun"):
    st.experimental_rerun()

radio_value = st.radio("Select2", ["Egg", "Spam", "Bacon", "Sausage"])
st.write(radio_value)

radio_value = st.radio("Select3", ["Egg", "Spam", "Bacon", "Sausage"])
st.write(radio_value)
