import streamlit as st
from functools import partial

class A:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
    
    def __hash__(self) -> int:
        return hash(self.name)
    def __eq__(self, other) -> bool:
        return (self.id == other.id) if str(type(self)) == str(type(other)) else False 
    
def on_change(index: int) -> None:
    new_name = st.session_state["new_name"]
    st.session_state["lst"][index].name = new_name

# Init state
if not "lst" in st.session_state:
    st.session_state["lst"] = [A(1, "one"), A(2, "two"), A(3, "three")]

# Fetch state
lst = st.session_state["lst"]

# Let user pick what to edit and if anything selected - show a field to change name
selected = st.selectbox("Select item", [""]+lst, key="something_else", format_func=lambda a: f"#{a.id} {a.name}" if a else "")
if selected:
    index = lst.index(selected)
    st.text_input("New name", selected.name, key="new_name", on_change=partial(on_change, index))
