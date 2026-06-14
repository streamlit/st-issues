import streamlit as st
import plotly.express as px
import pandas as pd

def get_demo_dataframe() -> pd.DataFrame:
    df = px.data.iris()  # iris is a pandas DataFrame
    df['Label_flag'] = "No"
    return df

if 'labels' not in st.session_state:
    st.session_state['labels'] = []
if 'df' not in st.session_state:
    st.session_state.df = get_demo_dataframe()
new_label = st.sidebar.text_input("Register Label")
if new_label and new_label not in st.session_state['labels']:
    st.session_state['labels'].append(new_label)
with st.sidebar.expander("Current Labels"):
    for label in st.session_state['labels']:
        st.write(label)

st.write(st.session_state.df)
color_map = {'YES': 'blue', 'NO': 'grey'}
fig = px.scatter(st.session_state.df, x="sepal_width", y="sepal_length", color = 'Label_flag', color_discrete_map = color_map)  #
fig.update_layout(showlegend=False)
fig.update_xaxes(visible=False)
fig.update_yaxes(visible=False)
fig.update_traces(marker_size=6)
fig.update_traces(hovertemplate = '%{customdata[0]}', customdata = st.session_state.df[['species']])
event = st.plotly_chart(fig, selection_mode=('box', 'lasso'), on_select="rerun")

with st.expander("See selection"):
    events = event['selection']['point_indices']
    events

if st.button("Apply"):
    st.session_state.df.loc[events, 'Label_flag'] = 'YES'
    st.rerun()
