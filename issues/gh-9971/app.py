import streamlit as st
import pandas as pd
import numpy as np

# Generate random data
data = pd.DataFrame({
    "Column 1": np.random.random(100),
    "Column 2": np.random.random(100),
})

# Title of the app
st.title("Streamlit Data Editor Example")

# Display editable data editor
st.data_editor(data, use_container_width=True)
