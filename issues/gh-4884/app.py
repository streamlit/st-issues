import streamlit
from datetime import date

min_date = date(2029, 1, 1)
streamlit.session_state["with_min_value"] = min_date
streamlit.date_input("with_min_value", min_value=min_date, key="with_min_value")

max_date = date(2020, 12, 31)
streamlit.session_state["with_max_value"] = max_date
streamlit.date_input("with_max_value", max_value=max_date, key="with_max_value")
