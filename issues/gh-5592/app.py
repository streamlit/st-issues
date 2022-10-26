import streamlit as st


st.container()

col1, col2 = st.columns(2)
with col1:
    st.image(
        "https://images.all-free-download.com/images/graphiclarge/sunrise_winter_sunrise_skies_215551.jpg",
    )

if st.button("Ghost mode!"):
    sleep(5)
