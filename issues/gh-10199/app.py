import streamlit as st
import pandas as pd


@st.cache_data(ttl=3, show_spinner=True)
def get_table(table_name: str) -> list:
    return [{"name": "AUD"}, {"name": "USD"}, {"name": "EUR"}, {"name": "GBP"}]


def get_table_as_dataframe(table_name: str) -> pd.DataFrame:
    return pd.DataFrame(get_table(table_name=table_name))


currencies1 = get_table_as_dataframe("1")
currencies2 = get_table_as_dataframe("2")
currencies3 = get_table_as_dataframe("3")
currencies4 = get_table_as_dataframe("4")
currencies5 = get_table_as_dataframe("5")
currencies6 = get_table_as_dataframe("6")
currencies7 = get_table_as_dataframe("7")
currencies8 = get_table_as_dataframe("8")
currencies9 = get_table_as_dataframe("9")
currencies10 = get_table_as_dataframe("10")
currencies11 = get_table_as_dataframe("11")
currencies12 = get_table_as_dataframe("12")
currencies13 = get_table_as_dataframe("13")
currencies14 = get_table_as_dataframe("14")
currencies15 = get_table_as_dataframe("15")


st.markdown("### Top of the page")
st.table(currencies1)
st.table(currencies1)
st.table(currencies1)
st.table(currencies1)
st.table(currencies1)
st.multiselect(
    "What are your favorite currencies?",
    currencies1["name"],
)
st.text_input("Text")
