import datetime

import pytz
import streamlit as st


@st.experimental_memo
def f(x: datetime.datetime):
    return x


t = datetime.datetime.now()
t_pytz = pytz.timezone("UTC").localize(t)

# This works
st.write(f(t))

# This raises UnhashableParamError
st.write(f(t_pytz))
