import matplotlib.pyplot as plt
import streamlit

fig, ax = plt.subplots(1, 1, figsize=(30, 15))
streamlit.pyplot(fig, format="svg")
