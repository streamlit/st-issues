import pandas as pd
import streamlit as st
import numpy as np

df = pd.DataFrame(
    {
        "int64": pd.array([1, 2, 3, 4, 5], dtype="Int64"),
        "int32": pd.array([1, 2, 3, 4, 5], dtype="Int32"),
        "int16": pd.array([1, 2, 3, 4, 5], dtype="Int16"),
        "int8": pd.array([1, 2, 3, 4, 5], dtype="Int8"),
        "uint64": pd.array([1, 2, 3, 4, 5], dtype="UInt64"),
        "uint32": pd.array([1, 2, 3, 4, 5], dtype="UInt32"),
        "uint16": pd.array([1, 2, 3, 4, 5], dtype="UInt16"),
        "uint8": pd.array([1, 2, 3, 4, 5], dtype="UInt8"),
        "float64": np.random.rand(5),
        "float32": pd.array(np.random.rand(5), dtype="float32"),
        "float16": pd.array(np.random.rand(5), dtype="float16"),
    }
)

#The data frame is created in the previous step.
style = df.style.bar(color=['#33FFCC', '#d65f5f'], align="left",width=50) 
style = style.set_properties(**{'background-color': '#111111', 'color': '#ffffff','font-size':'0.9em' ,'text-align': 'right','font-family': "Meiryo" }) 
style = style.set_precision(3)
st.sidebar.dataframe(style,height=500)
