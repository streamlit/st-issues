import streamlit as st
import pandas as pd
import time

df = pd.DataFrame({"steps":[0,1,2,3],"values": [4,2,1.4,0.9]})
my_chart = st.line_chart(df, x="steps", y="values")
df_new = pd.DataFrame({"steps":[4,5,6],"values": [0.5,0.3,0.5]})
time.sleep(3)
my_chart.add_rows(df_new)
