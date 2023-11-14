import pandas as pd
import streamlit as st
import numpy as np

st.title("This works")
chart_data = pd.DataFrame(np.random.randn(20, 3), columns=["a", "b", "c"])
st.bar_chart(chart_data)

st.title("This works")
chart_data = pd.DataFrame(np.random.randn(20, 3), columns=["a.b", "b.c", "c.d"])
st.bar_chart(chart_data)

st.title("This works")
chart_data = pd.DataFrame(np.random.randn(20, 1), columns=["a"])
st.bar_chart(chart_data)

st.title("This doesn't work")
chart_data = pd.DataFrame(np.random.randn(20, 1), columns=["a.b"])
st.bar_chart(chart_data)
