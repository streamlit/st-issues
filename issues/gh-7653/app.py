import streamlit as st

# Removing Deploy button: https://discuss.streamlit.io/t/removing-the-deploy-button/
DISABLE_DEPLOY_BUTTON_MARKDOWN = "<style>.stDeployButton {display:none;}</style>"

var = "foo"
st.markdown(
    DISABLE_DEPLOY_BUTTON_MARKDOWN + f"My inline code: `{var}`", unsafe_allow_html=True
)
