import streamlit as st

st.session_state.update({"key1": [1, 2], "key2": [1, 2]})

# multiselect that works
display1 = st.checkbox("Display multiselect with 1829 options (works)")
if display1:
    selection = st.multiselect(
        "Will keep values when hidden and redisplayed", list(range(1829)), key="key1"
    )
    st.write("Selection: ", selection)

# multiselect that fails to display default value
# in practice and with text, this issue starts to occur with around only 500 values
display2 = st.checkbox("Display multiselect with 1830 options (buggy)")
if display2:
    selection = st.multiselect(
        "Will keep values when hidden and redisplayed", list(range(1830)), key="key2"
    )
    st.write("Selection: ", selection)

st.write("---")
st.write("Session state:")
st.write(st.session_state)
