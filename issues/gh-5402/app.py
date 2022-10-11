import logging
import threading
import time

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx


@st.experimental_memo(ttl=1)
def function1(interval):
    interval = interval / 4
    logging.info("sleeping for %s seconds", interval)
    time.sleep(interval)
    logging.info("done sleeping for %s seconds", interval)
    return interval


def main():
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format)

    threads = []
    for index in range(25):
        x = threading.Thread(target=function1, args=(index,))
        # Hack to remove the following logging messages:
        #    `Thread 'Thread-123': missing ScriptRunContext`
        # see https://github.com/streamlit/streamlit/issues/1326
        add_script_run_ctx(x)
        threads.append(x)
        x.start()

    logging.info("Waiting for threads to finish")
    for thread in threads:
        thread.join()

    logging.info("done")
    st.write("done")


if __name__ == "__main__":
    main()
