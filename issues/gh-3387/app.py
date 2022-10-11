import streamlit as st


@st.cache(allow_output_mutation=True)
def storedVars(session):

    return {"a": ""}


var = storedVars(0)

newVar = ""

with st.form("my_form"):

    newVar = st.text_input("", value=var["a"])

    if st.form_submit_button("Execute"):

        var.update({"a": newVar})

        st.write(newVar, var)
