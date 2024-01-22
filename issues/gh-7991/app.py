import streamlit as st
import pandas as pd
import numpy as np

df = pd.DataFrame(np.random.rand(20).reshape(5, 4), columns=[f"col_{i}" for i in range(1, 5)])


st.write("directly display dataframe w/o subset")

st.data_editor(df, key="table1", hide_index=True)
st.success("`hide_index` works well!")

st.divider()

st.write("subset (`df.loc`) dataframe prior to display")

subset_df = df.loc[df.col_1 > 0.0]
st.data_editor(subset_df, key="table2", hide_index=True)
st.error("`hide_index` doesn't work!")

st.write("possible workaround")
subset_df.reset_index(drop=True, inplace=True)
st.data_editor(subset_df, key="table3", hide_index=True)

st.divider()

st.write("subset data using `df.iloc` is ok")

st.data_editor(df.iloc[:2], key="table4", hide_index=True)
st.success("`hide_index` works, it may because `iloc` creates view instead of copy.")
