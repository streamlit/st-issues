import streamlit as st
import pandas as pd

df = pd.DataFrame({"A": [1,2,3],"B":[4,5,6],"C":[7,8,9]})

a,b = st.columns([2,1])
a.data_editor(df, use_container_width=True)
