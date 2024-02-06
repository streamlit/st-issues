import streamlit as st
import pandas as pd

data = {
    "A": [1, 2, 3, 4, 5],
    "B": [1, 2, 3, 4, 5],
    "C": [1, 2, 3, 4, 5],
}

st.data_editor(pd.DataFrame(data), height=140, hide_index=True)
