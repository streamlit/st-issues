import streamlit as st
import pandas as pd

def update():
    if "data" not in st.session_state:
        return
    for row in st.session_state.shit["added_rows"]:
        st.session_state.data.loc[len(st.session_state.data)] = [row["Shit"]]
    st.session_state.data.reset_index(drop=True, inplace=True)

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Shit"])

options = [1, 2, 3]

if "data" in st.session_state:
    for i, row in st.session_state.data.iterrows():
        if row["Shit"] in options:
            options.remove(row["Shit"])

column_config = {
    "Shit": st.column_config.SelectboxColumn("Shit", options=options, required=True)
}

st.write(
    "st.data_editor with a selectbox that only lets you choose the options once."
)
st.write(
    "(The dataframe is checked for existing values, which are then removed from the available options)"
)
st.write(
    "The already existing values used to still be displayed correctly in the dataframe. Since one of the last updates they are now blank."
)

st.data_editor(
    st.session_state.data,
    num_rows="dynamic",
    hide_index=True,
    column_config=column_config,
    on_change=update,
    key="shit",
)

st.write("st.dataframe which displays actual dataframe values")

st.dataframe(st.session_state.data)
