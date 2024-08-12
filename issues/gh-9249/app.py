import streamlit as st
import pandas as pd
import os
import subprocess
import tempfile

validation_types = {'schema', 'duplicate', 'null', 'count', 'data'}

# Initialize a dictionary to keep track of processes
processes = {}
process_outputs = {}

# Initialize session state for processes and outputs
if 'processes' not in st.session_state:
    st.session_state['processes'] = {}
if 'process_outputs' not in st.session_state:
    st.session_state['process_outputs'] = {vt: {"stdout": "", "stderr": ""} for vt in validation_types}

# Initialize session state for running validation
if 'running_validation' not in st.session_state:
    st.session_state['running_validation'] = None

# Initialize placeholders for each validation type's buttons and output
output_placeholder = {vt: st.empty() for vt in validation_types}
clear_button_placeholder = {vt: st.empty() for vt in validation_types}

# Function to clear the output for a specific validation type
def clear_output(validation_type_inn, output_placeholder_inn, clear_button_placeholder_inn):
    # Clear the output in the session state for the specific validation type
    if validation_type_inn in st.session_state.get('process_outputs', {}):
        st.session_state['process_outputs'][validation_type_inn] = {"stdout": "", "stderr": ""}
    # Placeholder for output and clear button for each validation type
    output_placeholder_inn[validation_type_inn] = st.empty()
    clear_button_placeholder_inn[validation_type_inn] = st.empty()
    # Reset the running validation type only if it matches the validation type being cleared
    if st.session_state['running_validation'] == validation_type_inn:
        st.session_state['running_validation'] = None


# Function to retrieve and display the output for a specific validation type
def retrieve_validation_output(validation_type_inn):
    # Check if the validation type's output exists in the session state
    if validation_type_inn in st.session_state.get('process_outputs', {}):
        # Retrieve the output for the specific validation type
        output = st.session_state['process_outputs'][validation_type_inn]["stdout"]
        error = st.session_state['process_outputs'][validation_type_inn]["stderr"]

        # Display the output in a code block
        if output:
            st.code(output, language='bash')

        # Optionally, display the error in a separate code block or handle it differently
        if error:
            st.code(error, language='bash')

# Function to parse the validation status from subprocess output
def parse_validation_status(subprocess_output):
    if "Validation Status :: PASS" in subprocess_output:
        return "PASS"
    elif "Validation Status :: FAIL" in subprocess_output:
        return "FAIL"
    else:
        return "UNKNOWN"

def display_status_indicator(status):
    if status == "PASS":
        # Display a success indicator with custom styling
        st.markdown('<div class="custom-success"><span class="indicator-icon">✅️</span> Passed</div>', unsafe_allow_html=True)
    elif status == "FAIL":
        # Display a failure indicator with custom styling
        st.markdown('<div class="custom-error"><span class="indicator-icon">❌</span> Failed</div>', unsafe_allow_html=True)
    else:
        # Display an unknown status indicator with custom styling
        st.markdown('<div class="custom-warning"><span class="indicator-icon">⚠️</span> Validation Status Unknown</div>', unsafe_allow_html=True)


validation_types = {'schema', 'duplicate', 'null', 'count', 'data'}


# Main application
tab1, tab2, tab3 = st.tabs(
    ["**Schema Validation**", "**Duplicate Validation**", "**Null Validation**"])

with tab1:
    validation_type = 'schema'
    is_running = st.session_state.get('running_validation') == validation_type

    has_output = bool(st.session_state['process_outputs'][validation_type]["stdout"] or
                      st.session_state['process_outputs'][validation_type]["stderr"])

    # Display Run button
    col1, col2 = st.columns(2)
    with col1:
        # Place the button
        if st.button(f"**Run {validation_type.capitalize()} Validation**", disabled=is_running or has_output):
            st.session_state['process_outputs'][validation_type]["stdout"] = "Test Run"
            st.session_state['process_outputs'][validation_type]["stderr"] = ""
            # Mark this validation type as started
            st.session_state['validation_started_' + validation_type] = True
            st.session_state['running_validation'] = validation_type
            st.rerun()

    # Create a placeholder for the validation status indicator right below the button
    status_placeholder = st.empty()

    # Check if there is any output for the current validation type
    has_output = bool(st.session_state['process_outputs'][validation_type]["stdout"] or
                      st.session_state['process_outputs'][validation_type]["stderr"])
    has_error = bool(st.session_state['process_outputs'][validation_type]["stderr"])

    if has_output:
        if st.session_state.get('validation_started_' + validation_type, False):
            validation_status = parse_validation_status(
                st.session_state['process_outputs'][validation_type]["stdout"])

            # Update the placeholder with the validation status indicator
            with status_placeholder:
                display_status_indicator(validation_status)

    if has_output:
        with st.expander(f"**:grey[ Validation Result ]**", expanded=True):
            retrieve_validation_output(validation_type)

    # Placeholder for clear button
    clear_button_placeholder[validation_type] = st.empty()

    # Display the Clear button if there is output to clear
    if has_output:
        if clear_button_placeholder[validation_type].button(f"**Clear {validation_type.capitalize()} Check Result**"):
            clear_output(validation_type, output_placeholder, clear_button_placeholder)
            st.rerun()

with tab2:

    # Initialize session state variables
    if 'columns_for_duplicate_check' not in st.session_state:
        st.session_state['columns_for_duplicate_check'] = []
    if 'duplicate_check_columns' not in st.session_state:
        st.session_state['duplicate_check_columns'] = ''
    if 'columns_selected_for_dups' not in st.session_state:
        st.session_state['columns_selected_for_dups'] = None

    validation_type = 'duplicate'

    st.markdown(
        f'<p style="font-size:16px; color:green;"><b>Identify Duplicate Entries in Target Table using Primary Keys<b></p>',
        unsafe_allow_html=True)

    col11, col22 = st.columns(2)
    with col11:
        # Multiselect for selecting columns for duplicate check
        # No need to manually update st.session_state['columns_for_duplicate_check']
        columns_for_duplicate_check = st.multiselect('**:orange[Select Columns for Duplicate Check]**',
                                                     ['a','b'],
                                                     # default=st.session_state['columns_for_duplicate_check'],
                                                     key="columns_for_duplicate_check",
                                                     placeholder="Select Column(s)")
    # Use the local variable to generate the duplicate_check_columns string
    duplicate_check_columns = ', '.join(columns_for_duplicate_check)
    # Update the session state for duplicate_check_columns
    st.session_state['duplicate_check_columns'] = duplicate_check_columns
    # Check if columns_for_duplicate_check is not empty
    st.session_state['columns_selected_for_dups'] = bool(st.session_state['columns_for_duplicate_check'])
    # st.write('**Duplicate Check Columns :: ', ':green[{0}]**'.format(columns_for_duplicate_check))

    is_running = st.session_state['running_validation'] == validation_type

    has_output = bool(st.session_state['process_outputs'][validation_type]["stdout"] or
                      st.session_state['process_outputs'][validation_type]["stderr"])

    # Display Run button
    col1, col2 = st.columns(2)
    with col1:
        # Place the button
        if st.button(f"**Run {validation_type.capitalize()} Validation**", disabled=is_running or has_output or not st.session_state['columns_selected_for_dups']):
            st.session_state['process_outputs'][validation_type]["stdout"] = "Test Run"
            st.session_state['process_outputs'][validation_type]["stderr"] = ""
            # Mark this validation type as started
            st.session_state['validation_started_' + validation_type] = True
            st.session_state['running_validation'] = validation_type
            st.rerun()

    # Create a placeholder for the validation status indicator right below the button
    status_placeholder = st.empty()

    # Check if there is any output for the current validation type
    has_output = bool(st.session_state['process_outputs'][validation_type]["stdout"] or
                      st.session_state['process_outputs'][validation_type]["stderr"])
    has_error = bool(st.session_state['process_outputs'][validation_type]["stderr"])

    if has_output:
        if st.session_state.get('validation_started_' + validation_type, False):
            validation_status = parse_validation_status(
                st.session_state['process_outputs'][validation_type]["stdout"])

            # Update the placeholder with the validation status indicator
            with status_placeholder:
                display_status_indicator(validation_status)

    if has_output:
        with st.expander(f"**:grey[ Validation Result ]**", expanded=True):
            retrieve_validation_output(validation_type)

    # Placeholder for clear button
    clear_button_placeholder[validation_type] = st.empty()

    # Display the Clear button if there is output to clear
    if has_output:
        if clear_button_placeholder[validation_type].button(f"**Clear {validation_type.capitalize()} Check Result**"):
            clear_output(validation_type, output_placeholder, clear_button_placeholder)
            st.rerun()

with tab3:

    if 'columns_for_null_check' not in st.session_state:
        st.session_state['columns_for_null_check'] = []
    if 'null_check_type' not in st.session_state:
        st.session_state['null_check_type'] = None
    if 'columns_selected_for_nulls' not in st.session_state:
        st.session_state['columns_selected_for_nulls'] = None
    if 'null_check_on' not in st.session_state:
        st.session_state['null_check_on'] = None

    validation_type = 'null'

    st.markdown(
        f'<p style="font-size:16px; color:green;"><b>Ensure No Null Values in Not Null Fields<b></p>',
        unsafe_allow_html=True)
    # Check if this validation type is currently running

    col11, col22 = st.columns(2)
    with col11:
        # Multiselect for selecting columns for null check
        columns_for_null_check = st.multiselect('**:orange[Select Columns for Null Check]**',
                                                ['c','d'],
                                                # default=st.session_state['columns_for_null_check'],
                                                key="columns_for_null_check",
                                                placeholder="Select Column(s)")

    # Check if columns_for_duplicate_check is not empty
    st.session_state['columns_selected_for_nulls'] = bool(st.session_state['columns_for_null_check'])

    null_check_on = st.session_state.get('null_check_on', '**In Both Source & Target**')
    new_null_check_on = st.radio('**:orange[To Check nulls for the selected columns]**',
                                 ['**In Both Source & Target**', '**Only In Target**'],
                                 index=0 if null_check_on == '**In Both Source & Target**' else 1
                                 )
    if new_null_check_on != null_check_on:
        st.session_state['null_check_on'] = new_null_check_on
        clear_output(validation_type, output_placeholder, clear_button_placeholder)
        st.rerun()

    if st.session_state['null_check_on'] == '**In Both Source & Target**':
        st.session_state['null_check_type'] = 'both'
    else:
        st.session_state['null_check_type'] = 'target'

    is_running = st.session_state['running_validation'] == validation_type

    has_output = bool(st.session_state['process_outputs'][validation_type]["stdout"] or
                      st.session_state['process_outputs'][validation_type]["stderr"])

    # Display Run button
    col1, col2 = st.columns(2)
    with col1:
        # Place the button
        if st.button(f"**Run {validation_type.capitalize()} Validation**", disabled=is_running or has_output or not st.session_state['columns_selected_for_nulls']):
            st.session_state['process_outputs'][validation_type]["stdout"] = "Test Run"
            st.session_state['process_outputs'][validation_type]["stderr"] = ""
            # Mark this validation type as started
            st.session_state['validation_started_' + validation_type] = True
            st.session_state['running_validation'] = validation_type
            st.rerun()

        # st.divider()

    # Create a placeholder for the validation status indicator right below the button
    status_placeholder = st.empty()

    # Check if there is any output for the current validation type
    has_output = bool(st.session_state['process_outputs'][validation_type]["stdout"] or
                      st.session_state['process_outputs'][validation_type]["stderr"])
    has_error = bool(st.session_state['process_outputs'][validation_type]["stderr"])

    if has_output:
        if st.session_state.get('validation_started_' + validation_type, False):
            validation_status = parse_validation_status(
                st.session_state['process_outputs'][validation_type]["stdout"])

            # Update the placeholder with the validation status indicator
            with status_placeholder:
                display_status_indicator(validation_status)

    if has_output:
        with st.expander(f"**:grey[ Validation Result ]**", expanded=True):
            retrieve_validation_output(validation_type)

    # Placeholder for clear button
    clear_button_placeholder[validation_type] = st.empty()

    # Display the Clear button if there is output to clear
    if has_output:
        if clear_button_placeholder[validation_type].button(f"**Clear {validation_type.capitalize()} Check Result**"):
            clear_output(validation_type, output_placeholder, clear_button_placeholder)
            st.rerun()
