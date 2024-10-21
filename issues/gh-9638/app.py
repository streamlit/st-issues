import classDef as cd
import streamlit as st

def initObj():
    st.session_state.testObj = cd.testclass() 
    
st.button("Initialize", on_click=initObj) 
    
st.button("Rerun") 

if "testObj" in st.session_state:
    st.write("isinstance working? - " + str(isinstance(st.session_state.testObj, cd.testclass)))
else:
    st.write("Not initialized")
