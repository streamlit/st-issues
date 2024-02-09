import streamlit as st

help = """Some code block:

```
select * 
from table
```

"""

st.metric("Ice-creams", 13, help=help)
