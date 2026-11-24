"""
Reproduction for GitHub Issue #18071
Title: st.data_editor NumberColumn drops not allowed characters without any feedback
URL: https://github.com/streamlit/streamlit/issues/18071

Expected: Typing "1,23" into a NumberColumn cell is not silently committed as a
          different number.
Actual:   The "," keystroke is discarded and 123 is committed as a normal edit.
Reported version: 1.52.2 (also 1.67.0)
"""

import pandas as pd

import streamlit as st

st.title("Issue #18071: NumberColumn silently drops rejected characters")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/18071)")

st.header("Issue Overview")
st.write(
    "**Expected:** Input the number editor cannot accept is shown as invalid "
    "(or rejected visibly), never committed as a different number."
)
st.error(
    "**Actual (bug):** Rejected characters are stripped while typing. "
    "`1,23` commits `123` and `1a2` commits `12`, with no warning."
)

st.divider()

st.header("Bug Demonstration")
st.write(
    """
**Steps** (browser language English, so `.` is the decimal separator):
1. Double-click the Factor cell in the first row and type `1,23`, then press Enter.
2. Do the same in the second row with `1.23`.
3. Compare the returned values below: the first row is `123.0`, not `1.23`.
"""
)

bug_df = pd.DataFrame(
    {"Item": ["Type 1,23 here", "Type 1.23 here"], "Factor": [0.1, 0.1]}
)
bug_edited = st.data_editor(
    bug_df,
    column_config={"Factor": st.column_config.NumberColumn("Factor", format="plain")},
    hide_index=True,
    key="bug_editor",
)
st.write("Returned Factor values:")
st.code(repr(bug_edited["Factor"].tolist()))

st.divider()

st.header("Workaround")
st.write(
    "Use a `TextColumn` with a `validate` regex so invalid text is kept and "
    "highlighted, then convert to a number in Python (accepting `,` or `.` as "
    "the decimal separator). This loses numeric sorting and right alignment."
)

workaround_df = pd.DataFrame(
    {"Item": ["Type 1,23 here", "Type 1.23 here"], "Factor": ["0.1", "0.1"]}
)
workaround_edited = st.data_editor(
    workaround_df,
    column_config={
        "Factor": st.column_config.TextColumn(
            "Factor (text)", validate=r"^-?\d+([.,]\d+)?$"
        )
    },
    hide_index=True,
    key="workaround_editor",
)
factors = pd.to_numeric(
    workaround_edited["Factor"].str.replace(",", ".", regex=False), errors="coerce"
)
st.write("Converted Factor values:")
st.code(repr(factors.tolist()), language=None)

st.divider()

st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
