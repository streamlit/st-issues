import numpy as np
import pandas as pd

import streamlit as st

@st.dialog("Dataframe")
def df_dialog():
    st.dataframe(
        pd.DataFrame(np.zeros((1000, 6)), columns=["A", "B", "C", "D", "E", "F"])
    )

if st.button("Open dialog"):
  df_dialog()
