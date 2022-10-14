import streamlit as st
import numpy as np
import pandas as pd

np.random.seed(0)
df = pd.DataFrame(np.random.normal(1, 1, size=100))
st.pyplot(df.plot(figsize=(25, 5)))
