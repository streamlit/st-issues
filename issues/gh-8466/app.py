import streamlit as st

st.multiselect(
            "Select 1 - works",
            options=["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"],
            default=["d", "e"],
        )
        st.multiselect(
            "Select 2 - works",
            options={"a", "b", "c", "d", "e", "f", "g", "h", "i", "j"},
            default={"d", "e"},
        )
        st.multiselect(
            "Select 3 - works",
            options=[],
            default=[],
        )
        st.multiselect(
            "Select 4- works ",
            options=list(),
            default=list(),
        )
        st.multiselect(
            "Select 5 - crash ", # with: StreamlitAPIException: Every Multiselect default value must exist in options
            options=set(),
            default=set(),
        )
