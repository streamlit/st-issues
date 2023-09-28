import streamlit as st

how_many_columns = st.slider("How many columns?", min_value=1, max_value=20, value=5, step=1, key="how_many_columns")
columns = st.columns(how_many_columns)
for i in range(how_many_columns):
    with columns[i]:
        st.number_input(f"Input for column {i+1}", key=f"column_{i+1}")
