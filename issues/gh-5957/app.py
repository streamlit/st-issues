import streamlit as st

genre = st.radio(
    "What\'s your favorite movie genre",
    ('Comedy', 'Drama', 'Documentary'))

st.info(f'{genre}', icon="ℹ️")
