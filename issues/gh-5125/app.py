import streamlit as st
import requests
import json
from copy import deepcopy
import time

def app():

    st.title('Scenarios')

    # ----------------------------- LOAD EXISTING SCENARIO ---------------------------------- #

    st.markdown(
        "### Top-down expectations ###  \n"
    )

    # ----------------------------- SET RATES ----------------------------- #

    st.markdown("  \n"
                "  \n"
                "**Expected pace of cash flows**  \n")

    rates = st.session_state['rates'] if 'rates' in st.session_state else {}
    cols = st.columns((2,2))
    with cols[0]:
        options = ['fast','slow']
        default = options.index(rates['cash flow speed']) if 'cash flow speed' in rates else 0
        rates['cash flow speed'] = st.radio(label='cash flow speed',
                            options = ['fast','slow'],
                            index=default,
                             key='cash flow speed')


    with st.expander('rate', expanded=False):
        with st.form('Add'):
            rate_name = st.selectbox("Select rate name", options=['calls','dist','loss'])
            default = rates[rate_name] if rate_name in rates else 0
            new_override = st.slider(f"Expected {rate_name}",
                                     min_value=float(-1 * 100),
                                     max_value=float(1 * 100),
                                     step=1.0, value=default * 100.0,
                                     format="%.1f%%") / 100.0
            submit = st.form_submit_button('Submit')
        if submit:
            placeholder = st.empty()
            try:
                rates[rate_name] = new_override
                placeholder.success('Override submitted successfully')
            except Exception as e:
                placeholder.error(e)
            finally:
                time.sleep(1)
                placeholder.empty()

    st.session_state['rates'] = rates
    st.write(rates)

if __name__ == '__main__':
    app()
