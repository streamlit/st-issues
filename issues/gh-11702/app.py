import plotly.express as px
import streamlit as st
import pandas as pd

# Set page config
st.set_page_config(page_title="Demo App", layout="wide")

# Sidebar
with st.sidebar:
    st.header("Sidebar")
    st.write("This is an expandable/collapsible sidebar")

# Main content
st.title("Demo Streamlit App")
st.write("This is the main content area. The sidebar can be collapsed using the arrow in the top-left corner.")


# Create sample data
df = pd.DataFrame({
    'category': ['A', 'B', 'C', 'D', 'E'],
    'values': [23, 45, 56, 78, 32]
})

# Create a plotly bar chart
fig = px.bar(df, x='category', y='values',
             title='Sample Bar Chart')

# Display the chart in Streamlit
st.plotly_chart(fig, use_container_width=True)
