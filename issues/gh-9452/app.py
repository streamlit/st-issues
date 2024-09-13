import streamlit as st


columns_ = st.columns([9,1.5,1.5])
with columns_[1].popover("hi"):
    st.toggle("test", help=f"""
                             View statistics of all damage done at each skill level only.  
                             This includes all damage done at each player level available at  
                             each skill level.
                            """)

with columns_[2].popover("hi"):
    st.toggle("test 2", help=f"""
                             View statistics of all damage done at each skill level only.  
                             This includes all damage done at each player level available at  
                             each skill level.
                            """)
