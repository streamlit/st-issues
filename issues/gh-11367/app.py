import streamlit as st

def on_click_callback():
    st.toast("This is a toast notification!", icon="🔔")

@st.dialog(title="Streamlit Toast Notification", width="large")
def toast_notification():
   st.markdown("## Toast Notification")
   st.button("Show Toast", on_click=on_click_callback)

if st.button("Show Dialogue"):
    toast_notification()
