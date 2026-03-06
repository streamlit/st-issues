import time

import streamlit as st


@st.cache_data(ttl="10s")
def foo():
    time.sleep(2)


section = st.segmented_control("Section", ["S1", "S2"])

if section == "S1":
    st.markdown("- S1.1")
    st.markdown("- S1.2")
    st.markdown("- S1.3")
    st.markdown("- S1.4")
elif section == "S2":
    (tab,) = st.tabs(["S2.Tab"])
    foo()
    tab.markdown("S2 Lorem")
