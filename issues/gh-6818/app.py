import asyncio
import time

import streamlit as st


async def run_chronometer(container):
    while st.session_state["chrono_running"]:
        st.session_state["chrono_stop_ts"] = time.time()
        run_time = (
            st.session_state["chrono_stop_ts"] - st.session_state["chrono_start_ts"]
        )
        container.subheader(f"{run_time:.2f}")
        await asyncio.sleep(0.01)


def init_chrono():
    st.session_state["chrono_running"] = False
    st.session_state["chrono_start_ts"] = None
    st.session_state["chrono_stop_ts"] = None


if "chrono_running" not in st.session_state:
    init_chrono()

st.header("Chronometer")
col1_run, col2_run = st.columns(2)
container = st.empty()
col1_save, col2_save = st.columns(2)

# buttons to run chronometer
with col1_run:
    if st.button("Start", use_container_width=True):
        st.session_state["chrono_start_ts"] = time.time()
        st.session_state["chrono_running"] = True
        st.session_state["chrono_stop_ts"] = None

with col2_run:
    if st.button("Stop", use_container_width=True):
        st.session_state["chrono_running"] = False

# fill container when chrono is not running
if not st.session_state["chrono_running"]:
    if not st.session_state["chrono_stop_ts"]:
        container.subheader(f"{0.0:.2f}")
    else:
        run_time = round(
            st.session_state.chrono_stop_ts - st.session_state.chrono_start_ts, 2
        )
        container.subheader(f"{run_time:.2f}")

# buttons to save chronometer result
with col1_save:
    if st.button(
        "Save",
        disabled=(not st.session_state["chrono_stop_ts"]),
        use_container_width=True,
    ):
        st.write("Saved time:", run_time)

with col2_save:
    if st.button(
        "Delete",
        disabled=(not st.session_state["chrono_stop_ts"]),
        use_container_width=True,
    ):
        init_chrono()
        st.experimental_rerun()

# run chronometer asynchronously
asyncio.run(run_chronometer(container))
