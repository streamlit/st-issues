import streamlit as st


"# Unicode str"

error_message = "'bla' does not match \*'^[0-9]{8}_[A-Z]+[0-9]+_[0-9]+_[A-Z0-9]+$'\*"

st.code(type(error_message))

"## OK"
st.code(error_message)

"## Bug: some '_' are missing!!!"
st.write(error_message)
st.warning(error_message)
st.error(error_message)



"# Byte str"

error_message = b"'bla' does not match '^[0-9]{8}_[A-Z]+[0-9]+_[0-9]+_[A-Z0-9]+$'"

st.code(type(error_message))

"## OK"
st.code(error_message)
st.write(error_message)

"## Bug: some '_' are missing!!!"
st.warning(error_message)
st.error(error_message)
