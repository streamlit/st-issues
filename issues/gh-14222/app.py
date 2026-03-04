import streamlit as st

user_query = st.text_area(
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit 🐕 !",
    value="""Lorem ipsum dolor sit amet, consectetur adipiscing elit :
    - Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ;
    - Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris ;
    - Duis aute irure dolor in reprehenderit in voluptate velit esse ;
    - Excepteur sint occaecat cupidatat non proident, sunt in culpa qui.""",
    height="content",
)
