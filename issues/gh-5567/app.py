import streamlit as st

if "records_data" not in st.session_state:
    st.session_state.records_data = [
        {
            "id": "1",
            "deleted": False,
        },
        {
            "id": "2",
            "deleted": False,
        },
        {
            "id": "3",
            "deleted": False,
        },
        {
            "id": "4",
            "deleted": False,
        },
        {
            "id": "5",
            "deleted": False,
        }
    ]


def soft_delete(rec):
    rec["deleted"] = True


st.title("Dynamic expanders demo!")

for record in st.session_state.records_data:
    if not record["deleted"]:
        with st.expander(f"Details {record['id']}"):
            name = st.text_input(
                "Name",
                key=f"Name{record['id']}"
            )
            address = st.text_input(
                "Address",
                key=f"Address{record['id']}"
            )
            btn = st.button(
                "Delete",
                key=f"Delete{record['id']}",
                on_click=soft_delete,
                args=[record],
            )

