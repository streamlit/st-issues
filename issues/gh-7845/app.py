import streamlit as st

guess = st.chat_input("정답입력")

if guess:
  st.write(guess)
