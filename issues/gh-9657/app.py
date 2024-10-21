import datetime
import streamlit as st

class EES():
    amount: int = 0

if 'ees' not in st.session_state:
    st.session_state.ees = EES()
    st.session_state.ees.amount = 1
    st.session_state.logs = []

st.write('before', datetime.datetime.now(), st.session_state.ees.amount)

value = st.number_input("Value", min_value=0, value=st.session_state.ees.amount)

if value != st.session_state.ees.amount:
    msg = 'number changed'
    st.write('after', datetime.datetime.now(), value, st.session_state.ees.amount, msg)
    st.session_state.ees.amount = value
    # st.rerun()
else:
    msg = 'no change'

st.session_state.logs.append(str([value, msg]))

st.write('end', datetime.datetime.now(), st.session_state.ees.amount)

st.write('change log', st.session_state.logs)
