from datetime import datetime, timedelta

import streamlit as st

MIN_DATE = datetime(2022, 1, 1)

if "data_inicio" not in st.session_state:
    st.session_state.data_inicio = datetime.now() - timedelta(days=30)

if "data_fim" not in st.session_state:
    st.session_state.data_fim = datetime.now()

now = datetime.now()
st.session_state.data_inicio = st.date_input(
    label="Data Inicial",
    min_value=MIN_DATE,
    value=st.session_state.data_inicio,
    max_value=now,
    format="DD/MM/YYYY",
)
st.session_state.data_fim = st.date_input(
    label="Data Final",
    min_value=MIN_DATE,
    value=st.session_state.data_fim,
    max_value=now,
    format="DD/MM/YYYY",
)
