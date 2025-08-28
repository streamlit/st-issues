import streamlit as st


pdf_file = st.file_uploader("Upload a PDF file", type="pdf")
if pdf_file:
    st.write(f"PDF uploaded: {pdf_file.name}")
    st.pdf(pdf_file)


image_file = st.file_uploader("Upload a image file", type="png")
if image_file:
    st.write(f"Image uploaded: {image_file.name}")
    st.image(image_file)
