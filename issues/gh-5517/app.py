import streamlit as st

count_of_files = 60
progress_bar = st.progress(0.0)
counter = 0
file_paths = [str(i) for i in range(count_of_files)]

for file in file_paths:
    print(counter)
    progress_bar.progress(counter + (1 / count_of_files))
    counter += float(1 / count_of_files)
