import streamlit as st

st.checkbox("A")
st.checkbox("B")
st.checkbox("C")
left, right = st.columns(2)
with left:
    st.checkbox("D")
    st.checkbox("E")
    st.checkbox("F")
with right:
    st.checkbox("G")
    st.checkbox("H")
    st.checkbox("I")
    st.empty()  # Work around spacing issue with the last item in the column.
