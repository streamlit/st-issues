import streamlit as st


if 'ctr' not in st.session_state:
    st.session_state['ctr'] = 0

def uploader_callback():
    st.session_state['ctr'] += 1
    print('Uploaded file #%d' % st.session_state['ctr'])

st.write("Callback calls:", st.session_state['ctr'])
st.file_uploader(label="File uploader", on_change=uploader_callback, key="file_uploader")
