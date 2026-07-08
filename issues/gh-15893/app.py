"""Reproduction for GitHub Issue #15893
Title: st.tabs collapses into a stacked column after certain session-state interactions on 1.59.0 (works on 1.58.x)
URL: https://github.com/streamlit/streamlit/issues/15893

Expected: st.tabs() renders as a tab widget across all reruns, regardless of
          session-state activity elsewhere in the script.
Actual:   On 1.59.0, after a chain of nested widget interactions the tab widget
          flattens: all tab contents render as a single scrollable column with
          no tab bar. Reloading the page restores the tabs.
Reported version: 1.59.0 (broken), 1.58.x (works)

Same root cause as #15892: a widget rerun inside a tab collapses the st.tabs
container. Both trace to the st.tabs DOM rework that migrated from
baseui/tabs-motion to react-aria-components (#15328, "Remove BaseWeb for Tabs").
"""

import numpy as np
import pandas as pd
import streamlit as st

st.title("Issue #15893: st.tabs collapses after session-state interactions")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/15893)")
st.warning(
    "This is the same underlying bug as "
    "[#15892](https://github.com/streamlit/streamlit/issues/15892) — a widget "
    "rerun inside a tab collapses the tab container."
)

st.header("Issue Overview")
st.write(
    "**Expected:** `st.tabs()` renders as a tab widget across all reruns, "
    "regardless of session-state activity elsewhere in the script."
)
st.error(
    "**Actual (Bug on 1.59.0):** After a nested widget interaction the tab bar "
    "disappears and every tab's content renders as a single stacked column."
)

st.divider()

st.header("Bug Demonstration")
st.write(
    """
**Steps:**
1. Interact with the button in the first tab ("Setup"), then
2. Change the "Training library" selectbox inside the expander below.
3. Observe: on 1.59.0 the tab bar vanishes and every tab's content stacks
   vertically. On 1.58.x the tabs keep working.
"""
)

rng = np.random.RandomState(0)
df = pd.DataFrame({"x": range(20), "y": rng.rand(20)})


def tab_content(name: str) -> None:
    st.metric("Section", name)
    with st.form(f"{name}_form"):
        st.text_input("Note", key=f"{name}_note")
        st.form_submit_button("Submit")
    if st.button("Run computation", key=f"{name}_run"):
        st.write("Computed.")
    with st.expander("Advanced settings"):
        choice = st.selectbox(
            "Training library",
            ["spectrum-a", "spectrum-b", "spectrum-c"],
            key=f"{name}_lib",
        )
        st.line_chart(df.assign(y=df["y"] * (len(choice))).set_index("x"))


names = ["Setup", "PLS", "CLS", "Water", "Export"]
for tab, name in zip(st.tabs(names), names):
    with tab:
        tab_content(name)

st.divider()

st.header("Workaround")
st.write("Pin `streamlit<1.59` (latest 1.58.x) until a fix is released.")

st.divider()

st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
