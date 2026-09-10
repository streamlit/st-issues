"""Reproduction for GitHub Issue #16909
https://github.com/streamlit/streamlit/issues/16909

Expected: Typing ".07" into the Margin cell commits 0.0700.
Actual: The leading decimal point is dropped and the cell commits 7.0000.
Reported version: Streamlit 1.61.1
"""

import pandas as pd
import streamlit as st

st.title("Issue #16909: Leading decimal is dropped")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/16909)")

st.write("**Expected:** Typing `.07` into the Margin cell commits `0.0700`.")
st.error("**Actual (bug):** The editor commits `7.0000`.")

st.subheader("Reproduction")
st.write(
    """
1. Double-click the Margin cell.
2. Type `.07` as three separate keystrokes.
3. Press Enter and observe the committed value below the editor.

Typing `0.07` or pasting `.07` works around the issue.
"""
)

edited_df = st.data_editor(
    pd.DataFrame({"Customer": ["A", "B"], "Margin": [12.0, 8.0]}),
    column_config={
        "Customer": st.column_config.TextColumn("Customer", width="small"),
        "Margin": st.column_config.NumberColumn("Margin", format="%.4f", step=0.0001, width="small"),
    },
    hide_index=True,
    width="content",
)

st.text(f"Committed margin: {edited_df.loc[0, 'Margin']:.4f}")

st.subheader("Environment")
st.code(f"Streamlit version: {st.__version__}")
