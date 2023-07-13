import streamlit as st
import pandas as pd


def onchange():
    st.session_state.file_changed = True

# initialize Dataframe and state variables
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame({'name': ["1", "2"], 'Type': None})
    st.session_state.file_changed = False
    st.session_state.loaded = False

# file upload
uploaded_file = st.file_uploader("Choose a file", on_change=onchange)
if uploaded_file is not None:
    st.session_state.loaded = True
    if st.session_state.file_changed == True:
        st.session_state.df = pd.read_json(uploaded_file)
        st.session_state.file_changed = False

# create editable Dataframe
edited_df = st.data_editor(
    st.session_state.df,
    num_rows="dynamic",
    hide_index=True,  # this is relevant for the workaround, not sure about the bug
    key='demo_df'
)

# bug: edited_df only contains the entire visualized content including added rows, if it was not loaded from file
# deleted rows are treated correctly though
st.write("edited_df:")
st.write(edited_df)
# path to workaround: the changes (from the loaded file) are visible in the df in session_state when accessed by key
st.write(st.session_state["demo_df"])
