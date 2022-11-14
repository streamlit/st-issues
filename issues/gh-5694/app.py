import streamlit as st

df = pd.DataFrame()
with st.expander("Test"):
    st.dataframe(df, use_container_width=True)
