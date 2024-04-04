import streamlit as st
import pandas as pd

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Shit", "Piss"])

st.set_page_config(page_title="MotorCAD Interface", layout="wide")

options = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

column_config = {
    "Shit": st.column_config.SelectboxColumn("Shit", options=options, required=True)
}

st.write(
    "st.data_editor which seems to break when a new row is added. Notice the following:"
)
st.write("  - The index will appear, eventhough 'hide_index' is set to true")
st.write(
    "  - The callback will not be called again, changes wont be represented in the underlying dataframe"
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


def update():
    if "data" not in st.session_state:
        return
    for row in st.session_state.shit["added_rows"]:
        st.session_state.data.loc[len(st.session_state.data)] = [row["Shit"], None]
    
    # The code below is required, otherwise the data_editor breaks.
    # Its commented out to show the behaviour.

    # st.session_state.data.reset_index(drop=True, inplace=True)
