import streamlit as st


# set up some dummy session state variables
if 'options' not in st.session_state:
    st.session_state.options = ['D', 'C', 'B', 'A', 'F', 'E']

st.session_state.selected_option = st.selectbox(
    label='Select an option',
    options=st.session_state.options,
)

st.markdown(f'You selected: {st.session_state.selected_option}')

# move the selected option to the front of the list if it is not already
if st.session_state.selected_option != st.session_state.options[0]:
    st.session_state.options.remove(st.session_state.selected_option)
    st.session_state.options.insert(0, st.session_state.selected_option)
