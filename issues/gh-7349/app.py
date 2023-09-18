import streamlit as st

class Thing:
    @property
    def name(self) -> str:
        return 'my name'

things = [Thing() for i in range(3)]

st.session_state['current thing'] = things[0]

st.radio('things', options=things, format_func=lambda thing: thing.name, key='current thing')
