import pandas as pd
import streamlit as st

df = pd.DataFrame({
    "col-a": ["sam", "joe"],
    "col-b": [42, 36]
})

styler = df.style.relabel_index(["Name", "Age"], axis="columns")
st.table(styler)
st.write(styler)
