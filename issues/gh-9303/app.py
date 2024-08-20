import time
import streamlit as st

@st.dialog('Test Dialog')
def test_dialog():
    with st.container(border=True):
        if st.button(label='Click Me', key='test_button'):
            st.success('Successful Login!')

            spinner_bar = st.progress(0)
            time.sleep(0.5)

            with st.spinner('Logging In...'):
                index = 1
                messages_to_user = [
                    'Doing Stuff #1',
                    'Doing Stuff #2',
                    'Doing Stuff #3'
                ]

                while index <= 3:
                    spinner_bar.progress(index/3, text=messages_to_user[index - 1])
                    index += 1
                    time.sleep(1)

if __name__ == '__main__':
    test_dialog()
