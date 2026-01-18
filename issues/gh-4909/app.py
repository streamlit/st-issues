from enum import Enum

import streamlit as st


class Colors(Enum):
    yellow = 1
    blue = 2


selected_colors = st.multiselect(
    "choose colors",
    list(Colors),
)
