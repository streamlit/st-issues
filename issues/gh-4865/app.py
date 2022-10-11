import pandas as pd
import streamlit as st
import numpy as np

temp_data1 = {"Full Column Name": ["Total", "b", "c", "d", "e"], "Data Column": [1.1234567, 2.2345678, 3.3456789, 4.4567890, 5.098765432]}
temp_df1 = pd.DataFrame(temp_data1)

temp_data2 = {"Full Column Name": ["Total", "g", "r", "d", "e"], "Data Column": [5.1234567, 4.2345678, 3.3456789, 2.4567890, 7.098765432]}
temp_df2 = pd.DataFrame(temp_data2)

temp_data3 = {"Full Column Name": ["Total", "a", "z", "x", "c"],
              "Data Column": [0.1234567, 0.2345678, 0.3456789, 1.4567890, 2.098765432]}
temp_df3 = pd.DataFrame(temp_data3)

rows = st.columns(2)
rows[0].markdown("### Test1")
rows[0].dataframe(temp_df1)
rows[1].markdown("### Test2")
rows[1].dataframe(temp_df2)

col1, col2 = st.columns(2)
col1.markdown("### Real data1")
col1.dataframe(temp_df1)

col2.markdown("### Real data2")
col2.dataframe(temp_df2)

col1, col2 = st.columns(2)
chart_data = pd.DataFrame(
     np.random.randn(20, 3),
     columns=['a', 'b', 'c'])

col1.line_chart(chart_data)

col2.line_chart(chart_data)