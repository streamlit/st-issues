"""Reproduction for GitHub Issue #15892
Title: st.tabs: widget rerun inside a tab renders all tabs' content stacked below the page (regression in 1.59.0)
URL: https://github.com/streamlit/streamlit/issues/15892

Expected: A widget rerun inside a tab re-renders that tab in place; the other
          tabs stay hidden behind the tab bar (1.58.0 behavior).
Actual:   On 1.59.0 the tab bar vanishes and the content of ALL tabs renders
          stacked vertically down the page after the rerun.
Reported version: 1.59.0 (broken), 1.58.0 (works)

Likely root cause: the st.tabs DOM rework that migrated from baseui/tabs-motion
to react-aria-components (#15328, "Remove BaseWeb for Tabs").
"""

import numpy as np
import pandas as pd
import streamlit as st

st.title("Issue #15892: st.tabs collapses after a widget rerun inside a tab")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/15892)")

st.header("Issue Overview")
st.write(
    "**Expected:** Changing a widget inside a tab re-renders that tab in place; "
    "the other tabs stay hidden behind the tab bar."
)
st.error(
    "**Actual (Bug on 1.59.0):** After the rerun the tab bar disappears and the "
    "content of *all* tabs is rendered stacked vertically down the page."
)

st.divider()

st.header("Bug Demonstration")
st.write(
    """
**Steps:**
1. Stay on the first tab ("All").
2. Change the "Date range" selectbox below from "A" to "B".
3. Observe: on 1.59.0 the tab bar vanishes and every tab's content stacks
   vertically. On 1.58.0 only the first tab re-renders in place.
"""
)

rng = np.random.RandomState(42)
df = pd.DataFrame({"x": range(20), "y": rng.rand(20)})


def tab_content(name: str) -> None:
    st.metric("Metric", name)
    st.dataframe(df.head(3))
    st.bar_chart(df.set_index("x"))
    st.line_chart(df.set_index("x"))
    st.subheader("Leaderboard")
    choice = st.selectbox("Date range", ["A", "B", "C"], key=f"{name}_sel")
    n = {"A": 5, "B": 10, "C": 15}[choice]
    st.bar_chart(df.head(n).set_index("x"))


names = ["All", "Indy", "Clarksville", "Fort Wayne"]
for tab, name in zip(st.tabs(names), names):
    with tab:
        tab_content(name)

st.divider()

st.header("Workaround")
st.write("Pin `streamlit<1.59` (latest 1.58.x) until a fix is released.")

st.divider()

st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
