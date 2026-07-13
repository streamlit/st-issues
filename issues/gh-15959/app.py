"""Reproduction for GitHub Issue #15959
Title: `st.multiselect` options render below `st.popover`
URL: https://github.com/streamlit/streamlit/issues/15959

Expected: When an st.multiselect is used inside an st.popover, opening the
          multiselect shows its options dropdown on top of the popover body.
Actual:   The options dropdown renders below (behind) the popover body, so the
          options are hidden / not clickable.
Reported version: 1.59.2

Analysis: This is a z-index/stacking regression introduced by PR #15339
("Remove BaseWeb for Popover"), which moved st.popover to @floating-ui/react.
The popover body is portalled to <body> at `theme.zIndices.popup`. st.multiselect
still uses BaseWeb, whose overlays render in a shared "BaseWeb layer host" that is
ALSO pinned to `theme.zIndices.popup`. Because both resolve to the same z-index,
stacking falls back to DOM order — and the popover's FloatingPortal is appended
after the (early-mounted) BaseWeb layer host, so the popover body paints on top of
the multiselect dropdown. Verified: both the popover body and the multiselect
dropdown resolve to z-index 1000060, and every option li is occluded by the
popover body (elementFromPoint at each option's center returns the popover body).
"""

import streamlit as st

st.title("Issue #15959: st.multiselect options render below st.popover")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/15959)")

st.header("Issue Overview")
st.write(
    "**Expected:** Opening an `st.multiselect` inside an `st.popover` shows its "
    "options dropdown **on top of** the popover body."
)
st.error(
    "**Actual (Bug):** The options dropdown renders **behind** the popover body, "
    "so the options are hidden and cannot be selected."
)

st.divider()

st.header("Bug Demonstration")
st.write(
    """
**Steps:**
1. Click **Popover (multiselect)** below.
2. Click the **Multiselect** input to open its options.
3. Observe: the `option_1` / `option_2` list is hidden behind the popover body.
"""
)

with st.popover("Popover (multiselect)"):
    st.multiselect("Multiselect", ["option_1", "option_2"], key="ms_in_popover")

st.divider()

st.header("Controls (render correctly)")
st.write(
    "For comparison, `st.selectbox` was already migrated off BaseWeb and layers "
    "correctly inside a popover, and a multiselect outside any popover is fine too."
)

with st.popover("Popover (selectbox control)"):
    st.selectbox("Selectbox", ["option_1", "option_2"], key="sb_in_popover")

st.multiselect(
    "Multiselect (outside popover — control)",
    ["option_1", "option_2"],
    key="ms_outside",
)

st.divider()

st.header("Root Cause")
st.markdown(
    """
Introduced by PR [#15339](https://github.com/streamlit/streamlit/pull/15339)
("Remove `BaseWeb` for `Popover`"), which migrated `st.popover` to
`@floating-ui/react`:

- The **popover body** is portalled to `document.body` with
  `zIndex: theme.zIndices.popup !important`
  (`Popover/styled-components.ts` → `StyledPopoverBody`).
- `st.multiselect` still uses **BaseWeb**, whose overlays render in a shared
  "BaseWeb layer host" (created in `RootStyleProvider.tsx`) that is **also**
  pinned to `theme.zIndices.popup`.
- Both resolve to the **same** z-index (`1000060`), so stacking falls back to
  **DOM order**. The BaseWeb layer host mounts early (at app startup); the
  popover's `FloatingPortal` is appended later (when opened), so the popover body
  wins the tie and paints over the dropdown.

Before #15339, `st.popover` was itself a BaseWeb overlay in the same layer host,
so a later-opened dropdown naturally stacked above it — hence the regression.
This likely also affects other still-on-BaseWeb overlays inside a popover
(e.g. `st.date_input` / `st.time_input`).
"""
)

st.divider()

st.header("Workaround")
st.markdown(
    "No clean user-side workaround. Using `st.selectbox` (single-select) instead of "
    "`st.multiselect` inside the popover avoids the issue where possible, since the "
    "selectbox is already migrated off BaseWeb."
)

st.divider()

st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
