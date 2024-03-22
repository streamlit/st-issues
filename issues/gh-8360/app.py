import streamlit as st
import time

if 'foo' not in st.session_state:
    st.write('Setting state')
    st.session_state['foo'] = 'bar'

if st.button('Run'):
    # Allow for forward message queue to flush button element
    time.sleep(1)

    del st.session_state['foo']
    st.rerun()
