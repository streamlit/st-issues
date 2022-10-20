import streamlit as st

if "users_data" not in st.session_state:
    st.session_state.users_data = [
        {
            "id": "1",
            "username": "kajarenc",
            "address": "",
            "deleted": False,
        },
        {
            "id": "2",
            "username": "savva",
            "address": "",
            "deleted": False,
        },
        {
            "id": "3",
            "username": "john",
            "address": "",
            "deleted": False,
        },
        {
            "id": "4",
            "username": "mike",
            "address": "",
            "deleted": False,
        },
        {
            "id": "5",
            "username": "dan",
            "address": "",
            "deleted": False,
        }
    ]


def soft_delete(user):
    user["deleted"] = True


st.title("Dynamic expanders demo!")

for user in st.session_state.users_data:
    if not user["deleted"]:
        with st.expander(f"Details {user['id']}"):
            name = st.text_input(
                "Name",
                value=user["username"],
                key=f"Name{user['id']}"
            )
            address = st.text_input(
                "Address",
                value=user["address"],
                key=f"Address{user['id']}"
            )
            btn = st.button(
                "Delete",
                key=f"Delete{user['id']}",
                on_click=soft_delete,
                args=[user],
            )
