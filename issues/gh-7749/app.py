import streamlit as st
import pandas as pd

# using session state, works ever other input:
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame({"In":[0,1,2],"Out":[0,0,0]})
st.session_state.df = st.data_editor(st.session_state.df)
st.session_state.df["Out"] = st.session_state.df["In"]**2
st.write(st.session_state.df)

# # works every input but the df is not updated in data_editor:
# df = pd.DataFrame({"In":[0,1,2],"Out":[0,0,0]})
# df = st.data_editor(df)
# df["Out"] = df["In"]**2
# st.write(df)
