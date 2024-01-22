import streamlit as st
from pandas import DataFrame

df = DataFrame([["www.google.com", "www.facebook.com", "me"]], columns=["col1", "col2", "col3"])
st.dataframe(
    data=df,
    column_config={
        "col1": st.column_config.LinkColumn(display_text="📝"),
        "col2": st.column_config.LinkColumn(display_text="📝"),
    })

styled_df = df.style \
    .highlight_between(subset="col3", left="me", right="me", props="color:red")
st.dataframe(
    data=styled_df,
    column_config={
        "col1": st.column_config.LinkColumn(display_text="📝"),
        "col2": st.column_config.LinkColumn(display_text="📝"),
    })
