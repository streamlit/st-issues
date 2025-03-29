import numpy as np
import pandas as pd

import streamlit as st

np.random.seed(0)
# Generate random data
data = 2000 * np.random.rand(1000, 30)
columns = [f"Column {i + 1}" for i in range(30)]
df = pd.DataFrame(data, columns=columns)


def df_on_change():
    st.toast("Edited a cell!")


df_editor = st.data_editor(
    df,
    use_container_width=True,
    num_rows="fixed",
    disabled=[f"Column {i + 1}" for i in range(29)],
    column_order=[f"Column {i + 1}" for i in range(30)],
    key="df_editor",
    on_change=df_on_change,
    row_height=20,
)
