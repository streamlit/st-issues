import time
import streamlit as st


temp_holder = st.empty()

for i in range(3):
    with temp_holder.container():
        with st.container():
            st.markdown("# First")
            st.markdown(f"Message {i} with some content")
            if i == 0:
                st.write(f"Special content for {i}")

        with st.container():
            st.markdown("# Second")
            st.write(f"Another message {i} with more content.")
            if i == 1:
                st.write(f"Special content for {i}")

        with st.container():
            st.markdown("# Third")
            st.write(f"Final message {i}.")
            if i == 2:
                st.write(f"Special content for {i}")
    time.sleep(1)
