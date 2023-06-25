import streamlit as st
import pandas as pd

df = pd.DataFrame({"A": [1, 2, 3, 4], "B": [1, 2, 3, 4]})
styled_df = df.style.format({"B": "{:.2f}€"})

if 'df' not in st.session_state:
    st.session_state.df = df
    st.session_state.styled_df = styled_df

col1, col2 = st.columns(2)

with col1:
    st.subheader("Styled df in session state")
    st.data_editor(
        st.session_state.styled_df,
        key="display",
        disabled=("B"),
    )

with col2:
    st.subheader("Styled df redefined each rerun")
    st.data_editor(
        styled_df,
        key="display2",
        disabled=("B"),
    )

st.write(st.session_state.styled_df == styled_df)
st.write("Streamlit version: ", st.__version__)
