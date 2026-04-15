from datetime import date

import streamlit as st

st.title("gh-14799: `st.date_input` min_value year grid bug")

st.markdown("""
The year picker grid incorrectly greys out years within the valid range.
Open each picker, click the year header, and compare the year grids.
""")

col1, col2 = st.columns(2)

with col1:
    st.date_input(
        "Picker — 2026-02-01 to 2029-02-01",
        value=date(2026, 2, 1),
        min_value=date(2026, 2, 1),
        max_value=date(2029, 2, 1),
        key="a",
    )
    st.caption("2029 should be selectable ✅")

with col2:
    st.date_input(
        "Picker — 2026-07-07 to 2029-02-01",
        value=date(2026, 7, 7),
        min_value=date(2026, 7, 7),
        max_value=date(2029, 2, 1),
        key="b",
    )
    st.caption("2029 is greyed out ❌ (but reachable via month arrows)")
