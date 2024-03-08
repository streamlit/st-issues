import streamlit as st
import pandas as pd

data = pd.read_json('{"Foo":{},"Bar":{},"FooBar":{}}')

st.data_editor(data = data,
    hide_index=True,
    num_rows='dynamic'
    )
