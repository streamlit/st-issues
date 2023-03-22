import datetime
import time
import psutil
import os
pid = os.getpid()


import cv2
import numpy as np
import streamlit as st

img = np.random.rand(600,600,3)

@st.cache_resource(ttl=1)
def get_memory(pid):
    process = psutil.Process(pid)

    # Get the memory usage in RAM
    memory_usage = process.memory_info().rss

    # Convert the memory usage to MB
    memory_usage_mb = memory_usage / (1024 * 1024)
    return(memory_usage_mb)
    #print(f"Total memory usage of all running Python processes: {mem_usage} bytes")


def get_image():
    # Get current date and time
    img_with_date = img.copy()
    now = datetime.datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S.%f")[:-3]
    cv2.putText(img_with_date, dt_string, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    return img_with_date

def app():
    if "page_open" not in st.session_state:
        st.session_state.page_open = True

    if "num_img" not in st.session_state:
        st.session_state.num_img = 0


    st.title("Test memory usage of st.image...")

    text_placeholder = st.empty()
    img_placeholder = st.empty()

    while "page_open" in st.session_state:
        text_placeholder.write(f"{st.session_state.num_img} {get_memory(pid):.2f}MB")
        img_placeholder.image(get_image())

        st.session_state.num_img += 1
        time.sleep(1/10)

    print("Session ended...")
    img_placeholder.empty()
    text_placeholder.empty()
    st.stop()
if __name__ == "__main__":
    app()
