import streamlit as st

with st.expander("PDF Viewer", expanded=False):
  st.pdf("https://pdfobject.com/pdf/sample.pdf")
