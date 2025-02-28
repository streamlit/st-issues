import streamlit as st
import pandas as pd

df = pd.DataFrame({
        "A": [1,2,3,4,5],
        "B": [6,7,8,9,10],
        "C": [11,12,13,14,15],
    })

cols = st.columns(3)
with cols[0]:
    st.write("original table")
    st.dataframe(df, hide_index=True)
    
with cols[1]:
    def bg_color(row):
        return ["background-color: yellow"] * len(row)
    
    st.write("styled df")
    styled_df = df.style.apply(bg_color, axis=1)
    st.dataframe(styled_df, hide_index=True)

with cols[2]:
    styled_df = styled_df.hide(["B"], axis="columns")    # obsolete: styled_df = styled_df.hide_columns(["B"])
    st.write("after hiding column B")
    st.dataframe(styled_df, hide_index=True)
