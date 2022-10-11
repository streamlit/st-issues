import streamlit as st

checkboxes = {k: st.checkbox(f"Checkbox {k}", value=True) for k in range(3)}

tabs = st.tabs([f"Tab {k}" for k, v in checkboxes.items() if v])

for tab, text in zip(tabs, checkboxes):
    with tab:
        st.write(f"Text {text}")
