import streamlit as st
import pandas as pd

# Cached data function that returns test data
@st.cache_data
def load_test_data():
    return pd.DataFrame({
        'id': ['item_1', 'item_2', 'item_3'],
        'type': ['TypeA', 'TypeB', 'TypeC'],
        'value': [100, 200, 300]
    })

st.title("Multiselect Bug Reproducer")

# Sidebar with reload button (matching original pattern)
with st.sidebar:
    st.header("Data Management")
    if st.button("🔄 Reload Data", help="Clear cache and reload"):
        load_test_data.clear()
        st.success("Cache cleared! Data will be reloaded.")
        st.rerun()

# Load data
df = load_test_data()

# Extract unique types (matching original pattern)
all_types = sorted(df['type'].dropna().unique())

# Sidebar filters (matching original pattern)
st.sidebar.header("Filters") 

# Create multiselect in sidebar with all types as default
selected_types = st.sidebar.multiselect(
    "Select Types",
    all_types,
    default=all_types,  # All selected by default
)

# Filter data based on selection
filtered_df = df.copy()
if selected_types:
    filtered_df = filtered_df[filtered_df['type'].isin(selected_types)]

# Show debug info that reveals the bug
st.write("### Debug Information:")
st.write(f"**Multiselect shows selected**: {selected_types}")
st.write(f"**Filtered data rows**: {len(filtered_df)}")
st.write(f"**Item IDs in filtered data**: {sorted(filtered_df['id'].tolist())}")

st.write("---")
st.write("### Steps to reproduce bug:")
st.write("1. Initially all types are selected → shows 3 rows")
st.write("2. **In sidebar, deselect 'TypeA'** → should show 2 rows")
st.write("3. **Click 'Reload Data' button in sidebar**")
st.write("4. **BUG**: Sidebar shows 'TypeB, TypeC' but filtered data includes all 3 rows")

st.write("### Show actual data:")
st.dataframe(filtered_df)
