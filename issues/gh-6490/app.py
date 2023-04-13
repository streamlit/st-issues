import streamlit as st

# This does not have the copy-to-clipboard button:
st.code(
    """
import streamlit as st

st.write("Hello world")
"""
)

# This works fine:
st.markdown(
    """
```python
import streamlit as st

st.write("Hello world")
```
"""
)
