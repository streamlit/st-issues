from typing import Union
import streamlit as st

class MyCustomClass1:
    def __init__(self):
        self.a = 1
        self.b = 2

class MyCustomClass2:
    def __init__(self):
        self.a = 1
        self.b = 2

types = Union[MyCustomClass1, MyCustomClass2]

@st.cache_data(hash_funcs={types: lambda x: x.a + x.b})
def cached_func(custom_class_obj: types):
    return custom_class_obj.a / custom_class_obj.b  # Just as an example

obj = MyCustomClass1()
result = cached_func(obj)

st.write(result)
