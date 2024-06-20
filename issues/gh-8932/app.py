import streamlit as st

st.title("Fragment Download")

@st.experimental_fragment()
def dl_button(file: int):
    filename = f"{file}.pdf"
    with open(filename, "rb") as f:
        st.download_button(
            label=f"Download {filename}",
            data=f,
            file_name=filename,
        )

for ix in range(10):
    dl_button(ix)
