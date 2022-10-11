import streamlit as st


def test_1(val_1, val_2):

    st.write(f"val_1: {val_1}")
    st.write("----------------")
    st.write(f"val_2: {val_2}")
    st.write("----------------")

    # This could be a CRUD function


def test_2(val_1_key, val_2_key):

    st.write(
        f"val_1_key: {st.session_state[val_1_key] if val_1_key in st.session_state else 'Key-Error'}"
    )
    st.write("----------------")
    st.write(
        f"val_2_key: {st.session_state[val_2_key] if val_2_key in st.session_state else 'Key-Error'}"
    )
    st.write("----------------")

    # This could be a CRUD function


def insert_database(id: int, text: str) -> None:

    with st.spinner(text="Writing to database"):

        st.write(id)
        st.write(text)


def prepare_insert_database(id: int, key_identifier: str):

    # This middleware function is not really generic... Probably there are variation which value is in the session_state and which is fixed
    insert_database(id=id, text=st.session_state[key_identifier])


def main():

    with st.expander("Example without forms"):

        st.text_area(label="Please enter values", key="text_refs")

        st.button(
            label="Submit",
            on_click=test_1,
            kwargs=dict(val_1=10, val_2=st.session_state.text_refs),
        )

        st.session_state["submit_v2_val1"] = 10

        st.button(
            label="Submit - V2",
            on_click=test_2,
            kwargs=dict(val_1_key="submit_v2_val1", val_2_key="text_refs"),
        )

    with st.expander("With forms"):

        with st.form(key="form_master_key", clear_on_submit=True):

            st.text_area(label="Please enter values", key="text_refs_form")

            test_val = 11
            st.session_state["submit_v2_val1_form"] = test_val

            # This doesn't work and the displayed value is one behind.
            st.form_submit_button(
                label="Submit with on-click-Event",
                on_click=test_1,
                kwargs=dict(val_1=10, val_2=st.session_state.text_refs_form),
            )

            # This works but submitting keys to function to retrieve the real values within the function. This feels not really pythonic
            # st.form_submit_button(label="Submit with on-click-Event and keys", on_click=test_2, kwargs=dict(val_1_key="submit_v2_val1_form", val_2_key="text_refs_form"))

    # Start examples

    st.header("Real-Example without Callback and Form")

    input_reference = st.text_input(
        "Please input text", key="real_example_no_callback_reference"
    )

    if st.button("Save data"):

        insert_database(id=0, text=input_reference)

    st.header("Real-Example with Callback and Form (Working)")

    with st.form(key="real_example_form", clear_on_submit=True):

        input_reference_2 = st.text_input(
            "Please input text", key="real_example_callback_reference"
        )

        st.form_submit_button(
            label="Save data",
            on_click=prepare_insert_database,
            kwargs=dict(id=0, key_identifier="real_example_callback_reference"),
        )

    st.header("Not working solution but the most elegant one (Broken)")

    with st.form(key="real_example_form_not_working", clear_on_submit=True):

        input_reference_2 = st.text_input(
            "Please input text", key="real_example_callback_reference_not_working"
        )

        st.form_submit_button(
            label="Save data",
            on_click=insert_database,
            kwargs=dict(
                id=0, text=st.session_state.real_example_callback_reference_not_working
            ),
        )

    if st.button(label="Clear-Cache"):
        for item in st.session_state:
            del st.session_state[item]


main()
