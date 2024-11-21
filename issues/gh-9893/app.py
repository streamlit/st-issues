import streamlit as st
import pandas as pd
import urllib.parse

meal = 'fish & chips: £9'
url = 'https://example.com/feedme?meal='+urllib.parse.quote_plus(meal)
st.write(url)

df = pd.DataFrame({'link': [url]})

columnConfig = {}
columnConfig['link'] = st.column_config.LinkColumn('Link', display_text='.*meal=(.*)')
st.dataframe(df,column_config=columnConfig)
