import streamlit as st

st.header(body = "Testing problem switching tabs")

@st.cache_data(ttl=None)
def cached_func_level4():
    return "test"

@st.cache_data(ttl=None)
def cached_func_level3():
    return cached_func_level4()

@st.cache_data(ttl=None)
def cached_func_level2():
    return cached_func_level3()

@st.cache_data(ttl=None)
def cached_func_level1():
    return cached_func_level2()

@st.cache_data(ttl=None)
def cached_func_level0():
    # If you iterate more times than 2000, the tab problem is even bigger
    for _ in range(2000):
        x = cached_func_level1()
    return x


# In this testing tabs I only print a value and execute the 
# "root" cached function, which calls other cached funcs
admin_tabs = st.tabs(["test1", "test2"])

with admin_tabs[0]:
    st.write("Hello")
    val = cached_func_level0()

with admin_tabs[1]:
    st.write("World!")
    val = cached_func_level0()
