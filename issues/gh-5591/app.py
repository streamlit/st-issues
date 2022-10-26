import streamlit as st


def page_display():
    page_name = st.session_state["page_name"]
    st.session_state[f'{page_name} number'] = st.number_input(
        "Input a number here",
        min_value=0, max_value=10000000,
        format="%d",
        value=st.session_state.get(f'{page_name} number', 100),
    )


def main_page():
    name = st.text_input("New Analysis Name",
                         value=f"Analyses {st.session_state['counter']}")
    st.button("Create New Analysis", on_click=create_new_analysis_callback, args=[name])


if "page_names_to_funcs" not in st.session_state:
    st.session_state["page_names_to_funcs"] = {
        "Compare Analyses": main_page,
    }
    st.session_state["counter"] = 1


def create_new_analysis_callback(new_name):
    st.session_state["page_names_to_funcs"][new_name] = page_display
    st.session_state["counter"] += 1
    st.session_state["page_name"] = new_name
    st.session_state[f'{new_name} load_counter'] = 1
    return


page_name = st.sidebar.selectbox("Select a page",
                                 st.session_state["page_names_to_funcs"].keys(),
                                 key='page_name')
st.session_state["page_names_to_funcs"][st.session_state["page_name"]]()
