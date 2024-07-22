import streamlit as st

if "i" not in st.session_state:
    st.session_state.i = 0

@st.experimental_fragment(run_every=0.1)
def counter ():
    st.write(f"annoying counter... {st.session_state.i}")
    st.session_state.i += 1

with st.empty():
    counter()

image = st.file_uploader("upload an image")
if image is not None:
    st.image(image)
