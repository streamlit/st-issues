import streamlit as st
import pandas as pd

with st.expander("Show Code"):
    st.code(
    """
import streamlit as st
import pandas as pd

col = st.columns(2)

col[0].write("show dataframe that use st.write")
col[0].write(pd.DataFrame({"a": range(10)}))

col[1].write("show dataframe that use st.dataframe")
col[1].dataframe(pd.DataFrame({"a": range(10)}))
"""
    )

col = st.columns(2)

col[0].write("show dataframe that use st.write")
col[0].write(pd.DataFrame({"a": range(10)}))

col[1].write("show dataframe that use st.dataframe")
col[1].dataframe(pd.DataFrame({"a": range(10)}))
