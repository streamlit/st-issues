import streamlit as st

project = st.selectbox("Select the project", options=[1, 2], key="project_selection")

if project == 1:
    dataset_option = []
elif project == 2:
    dataset_option = ["dataset1", "dataset2"]

dataset = st.selectbox("Select the dataset", options=dataset_option, key="dataset_selection", index=0 if len(dataset_option) > 0 else None)

if dataset is None:
    st.error("No datasets available.")
