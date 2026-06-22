"""Reproduction for GitHub Issue #15653
Title: The hover effect of st.date_input varies depending on the value of min_value
URL: https://github.com/streamlit/streamlit/issues/15653

Reported: hovering over calendar dates shows a hover effect for some `min_value`
          settings but not others.
Finding:  working as intended — the hover effect applies to *selectable* dates
          only. Out-of-range (disabled) dates never highlight. The apparent
          inconsistency is purely a function of which dates are enabled.
"""

from datetime import datetime, timedelta

import streamlit as st

st.title("Issue #15653: date_input hover effect vs. min_value")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/15653)")

st.header("Issue Overview")
st.write(
    "**Reported:** With `min_value` inside the current month, hovering over "
    "calendar dates shows no hover effect; with `min_value` in the previous "
    "month, a hover effect appears."
)
st.success(
    "**Finding (working as intended):** The hover highlight applies to "
    "**selectable** dates only. Disabled (out-of-range) dates never highlight. "
    "Changing `min_value` only changes *which* dates are selectable — the hover "
    "behavior itself is consistent."
)

st.divider()

st.header("Try it yourself")
st.write(
    """
**Steps:**
1. Open each calendar below and hover over the dates.
2. Hover over a **dark / enabled** date — the hover ring appears in **both** cases.
3. Hover over an early-month **grey / disabled** date such as **June 4** —
   no ring in Case A (out of range), but a ring in Case B (in range).
"""
)

today = datetime.now().date()

st.subheader("Case A — min_value within current month (7 days ago)")
st.caption(f"`min_value = {today - timedelta(days=7)}` → early-month days are DISABLED")
st.date_input(
    label="min_value = 7 days ago",
    key="case_a",
    value=None,
    max_value="today",
    min_value=(datetime.now() - timedelta(days=7)).date(),
    disabled=False,
)

st.subheader("Case B — min_value in previous month (31 days ago)")
st.caption(f"`min_value = {today - timedelta(days=31)}` → early-month days are ENABLED")
st.date_input(
    label="min_value = 31 days ago",
    key="case_b",
    value=None,
    max_value="today",
    min_value=(datetime.now() - timedelta(days=31)).date(),
    disabled=False,
)

st.divider()

st.header("Workaround")
st.write(
    "No workaround needed — this is expected behavior. Disabled dates are "
    "intentionally non-interactive and therefore do not show a hover effect."
)

st.divider()

st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
