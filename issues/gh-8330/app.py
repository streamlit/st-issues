import streamlit as st

long_text_with_explicit_line_breaks = '''
Call me Ishmael. 
Some years ago—never mind how 
long precisely—having little 
or no money in my purse, and nothing 
particular to interest me on shore, 
I thought I would sail about a little 
and see the watery part of the world. 
It is a way I have of driving off the spleen and 
regulating the circulation. 
Whenever I find myself growing grim about the mouth; 
whenever it is a damp, drizzly November in my soul; 
whenever I find myself involuntarily pausing before 
coffin warehouses, and bringing up the rear of every funeral I meet
'''

long_text_with_no_line_breaks = long_text_with_explicit_line_breaks.replace('\n', ' ')

st.toast(long_text_with_no_line_breaks)
st.toast(long_text_with_explicit_line_breaks)
