from typing import List, Any

import streamlit as st


def selectbox_with_query_storage(label: str, options: List[Any], query_param_name: str, **kwargs):
    default_index = 0
    current_query_params = st.experimental_get_query_params()
    current_value_params = current_query_params.get(query_param_name, [])
    current_value = None
    if len(current_value_params) == 1:
        current_value_str = current_value_params[0]
        current_value = type(options[0])(current_value_str)  # Convert to type based on first option.
        try:
            default_index = options.index(current_value)
        except ValueError:
            pass
    value = st.selectbox(label, options, index=default_index, **kwargs)
    if value != current_value:
        current_query_params[query_param_name] = value
        st.experimental_set_query_params(**current_query_params)
    return value


val = selectbox_with_query_storage("Remember me", ["a", "b", "c", "d", "e"], query_param_name="choice")
st.write(val)
