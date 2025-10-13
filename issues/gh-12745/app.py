"""
Reproduction for GitHub Issue #12745
Title: st.data_editor infers datatype int but float is expected
Issue URL: https://github.com/streamlit/streamlit/issues/12745

Description:
When using st.data_editor with session_state storage, if a user first inputs 
integer values and then tries to change them to floats, the data editor prevents 
entering decimal points. The issue occurs because data_editor infers the column 
type from the data passed to it, seeing only integers and incorrectly assuming 
an integer column.

Expected Behavior:
The data_editor should respect the NumberColumn config with float format and 
allow decimal input at all times.

Actual Behavior:
After storing integer values to session_state and rerunning, the data_editor 
no longer accepts decimal points.
"""

import pandas as pd
import streamlit as st


def btn_on_click():
    st.session_state.df_input = df_result


st.title("Issue #12745: Data Editor Int vs Float Type Inference")

st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/12745)")

st.header("Reproduction Steps")

st.write("""
1. Type **integer values** into the two fields (e.g., 1, 2)
2. Click the **"Store df to session state"** button
3. Try to input **float values** with decimals (e.g., 1.5, 2.5)
4. **BUG:** You cannot type the decimal point!
""")

st.divider()

st.header("Data Editor")

st.session_state.setdefault('df_input', pd.DataFrame(data=[None, None], columns=['number']))

df_result = st.data_editor(
    st.session_state.df_input,
    column_config={'number': st.column_config.NumberColumn(format='%.1f')},
)

st.button('Store df to session state', on_click=btn_on_click)

st.divider()

st.header("Current State")
st.write("**DataFrame in session_state:**")
st.write(st.session_state.df_input)
st.write(f"**Data type of 'number' column:** {st.session_state.df_input['number'].dtype}")

st.divider()

st.header("Expected vs Actual")
st.write("**Expected:** The data_editor should always accept float values when configured with a float format.")
st.write("**Actual:** After storing integer values, the data_editor infers int type and blocks decimal input.")

st.divider()

st.header("Workaround")
st.write("""
A workaround is to explicitly convert the datatype in the callback:

```python
def btn_on_click():
    st.session_state.df_input = df_result.astype({'number': 'float'})
```
""")

st.divider()

st.header("Environment Info")
st.code(f"""
Streamlit version: {st.__version__}
Python version: 3.11.9
OS: Windows 11 Enterprise
Browser: Microsoft Edge
""")

