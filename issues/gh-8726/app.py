import streamlit as st

import streamlit as st

st.write('Hello :sunglasses:') # Renders as "Hello 😎"
st.write('Hello :sunglasses') # Renders as "Hello", but should render as "Hello :sunglasses", in case the user is trying to type text with colons in.

st.write('email:example@hotmail.com') # Renders as "email @hotmail.com"
