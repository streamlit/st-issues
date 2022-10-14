from enum import Enum
import streamlit as st

class A(Enum):
    Var1 = 0

@st.cache
def get_enum_dict():
    return {A.Var1: "Hi"}

look_up_key = A.Var1
cached_value = get_enum_dict()
st.write("class id of look_up_key: {}".format(id(look_up_key.__class__)))
st.write("class id of cached key: {}".format(id(list(cached_value.keys())[0].__class__)))
st.write(cached_value[look_up_key])
