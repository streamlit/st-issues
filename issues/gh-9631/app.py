import streamlit as st

audio_recorded = st.experimental_audio_input("Record a voice message")

if audio_recorded:
    st.audio(audio_recorded)
