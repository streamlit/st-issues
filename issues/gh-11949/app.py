import streamlit as st
data = [{"name":'Ron', "id": 1}, {"name":'Fred', "id": 2}, {"name":'George', "id": 3}, {"name":'Fred', "id": 4}, {"name":'George', "id": 5}]

labels = [x["name"] for x in data]
options = [x["id"] for x in data]
dic = dict(zip(options, labels))

a = st.selectbox('Choose name', options=options, format_func=lambda x: dic[x])

st.write(a)
