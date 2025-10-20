"""
Reproduction for GitHub Issue #12815
Title: MultiselectColumn: inhomogeneous array shape error when adding new row to data editor with multiple columns
Issue URL: https://github.com/streamlit/streamlit/issues/12815

Description:
When using st.data_editor with a MultiselectColumn and dynamic rows enabled (num_rows="dynamic"),
adding a new row causes a ValueError when you select values in the multiselect column.

Expected Behavior:
Users should be able to add new rows to the data editor and select multiselect values without errors.

Actual Behavior:
Adding a row and selecting multiselect options triggers:
ValueError: setting an array element with a sequence. The requested array has an inhomogeneous 
shape after 1 dimensions. The detected shape was (2,) + inhomogeneous part.

Reported Version: Streamlit 1.50.0
"""

import pandas as pd
import streamlit as st

# === HEADER ===
st.title("Issue #12815: MultiselectColumn with Dynamic Rows")

st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/12815)")

# === ISSUE OVERVIEW ===
st.header("Issue Overview")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Expected Behavior")
    st.write("""
    - Users can add new rows to data editor with `num_rows="dynamic"`
    - Users can select values from MultiselectColumn
    - New row is added successfully with selected values
    """)

with col2:
    st.subheader("Actual Behavior (Bug)")
    st.error("""
    ❌ **ValueError occurs** when adding a new row and selecting multiselect options
    
    Error: `inhomogeneous array shape after 1 dimensions`
    """)

st.divider()

# === REPRODUCTION ===
st.header("🐛 Bug Demonstration")

st.write("""
**Instructions to reproduce the bug:**
1. Click the **"+" (Add row)** button at the bottom of the data editor below
2. In the new row, select **one or more categories** from the "App Categories" dropdown
3. Click anywhere outside the cell to confirm your selection
4. **Observe the error** that appears below the data editor
""")

st.warning("⚠️ The error occurs specifically when the data editor has BOTH a MultiselectColumn AND other column types (like CheckboxColumn).")

# Create the initial dataframe with multiselect columns
data_df = pd.DataFrame(
    {
        "category": [
            ["exploration", "visualization"],
            ["llm", "visualization"],
            ["exploration"],
        ],
        "is_active": [True, True, True],
    }
)

st.subheader("Buggy Data Editor")
st.write("Try adding a new row and selecting categories:")

try:
    edited_df = st.data_editor(
        data_df,
        hide_index=True,
        num_rows="dynamic",
        key="data_editor_buggy",
        column_config={
            "category": st.column_config.MultiselectColumn(
                "App Categories",
                help="The categories of the app",
                options=[
                    "exploration",
                    "visualization",
                    "llm",
                ],
                color=["#ffa421", "#803df5", "#00c0f2"],
                format_func=lambda x: x.capitalize(),
            ),
            "is_active": st.column_config.CheckboxColumn(
                "Active",
                help="Tick to include this app in the analysis.",
                default=True,
                required=True,
            ),
        },
    )
    
    st.success(f"✅ Data editor is working! Current rows: {len(edited_df)}")
    
    # Show the current data
    with st.expander("View current data", expanded=False):
        st.write(edited_df)
        
except Exception as e:
    st.error("❌ **BUG TRIGGERED!** Error occurred:")
    st.exception(e)
    st.write("This is the error that users encounter when adding rows with multiselect values.")

st.divider()

# === WORKAROUND ===
st.header("✅ Workaround")

st.write("""
**Temporary Workaround:** Use `num_rows="fixed"` to prevent adding new rows.

However, this defeats the purpose for users who need dynamic row addition.
""")

st.subheader("Data Editor with Fixed Rows (No Bug)")
st.write("This version works, but users cannot add rows:")

# Same config but with fixed rows
data_df_fixed = pd.DataFrame(
    {
        "category": [
            ["exploration", "visualization"],
            ["llm", "visualization"],
            ["exploration"],
        ],
        "is_active": [True, True, True],
    }
)

edited_df_fixed = st.data_editor(
    data_df_fixed,
    hide_index=True,
    num_rows="fixed",  # This prevents the bug but also prevents adding rows
    key="data_editor_fixed",
    column_config={
        "category": st.column_config.MultiselectColumn(
            "App Categories",
            help="The categories of the app",
            options=[
                "exploration",
                "visualization",
                "llm",
            ],
            color=["#ffa421", "#803df5", "#00c0f2"],
            format_func=lambda x: x.capitalize(),
        ),
        "is_active": st.column_config.CheckboxColumn(
            "Active",
            help="Tick to include this app in the analysis.",
            default=True,
            required=True,
        ),
    },
)

st.info("ℹ️ Notice: The '+ Add row' button is not available with num_rows='fixed'")

st.divider()

# === TECHNICAL DETAILS ===
st.header("Technical Details")

st.write("""
**Root Cause:** 

The bug occurs in `lib/streamlit/elements/widgets/data_editor.py` in the `_apply_row_additions()` function.
When adding a new row using:

```python
df.loc[index, :] = new_row
```

Pandas fails when `new_row` contains both:
- Scalar values (e.g., `True` from CheckboxColumn)
- List values (e.g., `["exploration", "visualization"]` from MultiselectColumn)

This causes a numpy array shape error because pandas cannot create a homogeneous array from mixed scalar/list types.

**Affected Component:** `st.data_editor` + `st.column_config.MultiselectColumn`

**Affected Streamlit Version:** 1.50.0 (and likely earlier versions)

**Regression:** Not reported as a regression

**Related Components:**
- `lib/streamlit/elements/widgets/data_editor.py` (lines 379, 385)
- `MemoryUploadedFileManager`
""")

with st.expander("View Expected Error Message", expanded=False):
    st.code("""
ValueError: setting an array element with a sequence. 
The requested array has an inhomogeneous shape after 1 dimensions. 
The detected shape was (2,) + inhomogeneous part.
    """, language="text")

st.divider()

# === ENVIRONMENT INFO ===
st.header("Environment Info")

st.code(f"""
Streamlit version: {st.__version__}
Python version: 3.11.13 (reported in issue)
Operating System: macOS 15.5 (reported in issue)
Browser: Chrome (reported in issue)
""")

st.divider()

# === TESTING NOTES ===
st.header("Testing Notes for Reviewers")

st.write("""
**To verify the bug:**
1. In the first data editor (labeled "Buggy Data Editor"), click the "+ Add row" button
2. In the new row, click on the "App Categories" cell
3. Select at least one category from the dropdown
4. Click outside the cell or press Enter
5. The error should appear immediately

**Expected fix:**
- Users should be able to add rows and select multiselect values without errors
- The data editor should handle mixed column types (lists and scalars) correctly
- Row addition should work seamlessly with MultiselectColumn

**Additional test cases:**
- Try adding multiple rows in sequence
- Try selecting different combinations of categories
- Try editing existing rows (this should work fine)
""")

