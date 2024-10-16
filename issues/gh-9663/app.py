import streamlit as st
import time

original_container = st.empty()
remaining_time_container = st.empty()
button_state = original_container.button("send code", key='get_code_button')
countdown_triggered = False
if button_state:
    if not countdown_triggered:
        countdown_triggered = True
        original_container.empty()
        disabled_button = True
        remaining_time = 5
        while remaining_time > 0:
            temp_button = remaining_time_container.button(f"Re-send({remaining_time})", disabled=disabled_button, key=f'resend_button_{remaining_time}')
            time.sleep(1)
            remaining_time -= 1
        remaining_time_container.empty()
        original_container.button("send code", key='get_code_button_again')

if st.button("hello"):
    st.write("hello")
