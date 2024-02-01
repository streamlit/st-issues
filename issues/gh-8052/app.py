import time

import pandas as pd
import streamlit as st


def get_df() -> pd.DataFrame:
    if st.session_state["df"] is None:
        with st.spinner("Computing expensive thing..."):
            time.sleep(2)
            st.session_state["df"] = pd.DataFrame({"a": [1, 2, 3], "b": [True, False, True]})

    return st.session_state["df"]


# Initialize state
if "df" not in st.session_state:
    st.session_state["df"] = None

# Get data
df = get_df()

# Display
tabs = st.tabs(["Tab 1", "Tab 2"])
with tabs[0]:
    edit1 = st.data_editor(df, disabled={"a"}, hide_index=True, num_rows="fixed", use_container_width=True, key="tab1")
with tabs[1]:
    edit2 = st.data_editor(df, disabled={"a"}, hide_index=True, num_rows="fixed", use_container_width=True, key="tab2")
