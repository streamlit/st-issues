"""Reproduction for GitHub Issue #15891
Title: "Download to CSV" export from st.dataframe excludes hierarchical column headers
URL: https://github.com/streamlit/streamlit/issues/15891

Expected: The CSV downloaded from the st.dataframe toolbar includes every level
          of a MultiIndex (hierarchical) column header.
Actual:   Only the lowest level of the column header is exported; the upper
          levels are dropped.
Reported version: 1.59.0
"""

import pandas as pd
import streamlit as st

st.title('Issue #15891: "Download to CSV" drops hierarchical column headers')
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/15891)")

st.header("Issue Overview")
st.write(
    "**Expected:** The built-in *Download to CSV* button in the `st.dataframe` "
    "toolbar exports **all** levels of a MultiIndex column header."
)
st.error(
    "**Actual (Bug):** Only the lowest header level is exported. For the table "
    "below, the top level (`2022` / `2023`) is missing from the CSV — you only "
    "get the `Q1`–`Q4` row."
)

st.divider()

st.header("Bug Demonstration")
st.write(
    """
**Steps:**
1. Hover over the dataframe below to reveal the toolbar (top-right).
2. Click the **Download as CSV** (⬇) button.
3. Open the downloaded file and compare it to the table.

**What you'll see:** the CSV header only contains `Q1,Q2,Q3,Q4,Q1,Q2,Q3,Q4` —
the `2022` / `2023` level is gone.
"""
)

first_level = ["2022", "2023"]
second_level = ["Q1", "Q2", "Q3", "Q4"]
multi_columns = pd.MultiIndex.from_product([first_level, second_level])

df = pd.DataFrame(
    [[23, 33, 22, 44, 45, 66, 31, 18], [11, 16, 47, 53, 78, 82, 9, 14]],
    index=["Sales", "Marketing"],
    columns=multi_columns,
)

st.dataframe(df)

st.divider()

st.header("Workaround")
st.write("Use `pandas.DataFrame.to_csv` (which preserves all header levels) together with `st.download_button`:")
st.code(
    """exported_df = df.to_csv()
st.download_button(
    "Download Table Data",
    exported_df,
    mime="text/csv",
)""",
    language="python",
)
st.download_button(
    "Download Table Data (workaround)",
    df.to_csv(),
    file_name="export_with_headers.csv",
    mime="text/csv",
)

st.divider()

st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
