# gh-15959: `st.multiselect` options render below `st.popover`

## Summary

When an `st.multiselect` is opened inside an `st.popover`, its options dropdown
renders *behind* the popover body instead of on top of it, so the options are
hidden and cannot be selected. Reported as a regression on 1.59.2.

## Finding

**Bug confirmed** on Streamlit 1.59.0, 1.59.1, and 1.59.2 (the reporter's
version). Verified with Playwright on each released build: after opening the
popover and clicking the multiselect, both option list items are painted behind
the popover body, and in all three the popover body and dropdown resolve to the
same z-index (`1000060`).

## Reproduction

- App: `st.multiselect("Multiselect", ["option_1", "option_2"])` inside
  `with st.popover("Popover"):` (the reporter's exact snippet).
- Method: headless Chromium via Playwright against a released-Streamlit
  `streamlit run` server. Opened the popover, clicked the multiselect input to
  open its dropdown, then measured geometry, effective z-index, and
  `document.elementFromPoint` at each option's center.

Key observations:

| Element | Effective z-index host | Result |
|---|---|---|
| Popover body (`stPopoverBody`) | `1000060` | painted on top |
| Multiselect dropdown (BaseWeb `li` options) | `1000060` | occluded |

`elementFromPoint` at the center of both `option_1` and `option_2` returns a
`<div>` **inside** the popover body (not the option) — i.e. 2/2 options are
occluded. Both overlays resolve to the same z-index (`1000060` =
`theme.zIndices.popup`), so DOM order decides and the popover body wins.

Control cases render correctly: `st.selectbox` inside a popover, and
`st.multiselect` outside any popover.

## Root Cause

Introduced by PR [#15339](https://github.com/streamlit/streamlit/pull/15339)
("Remove `BaseWeb` for `Popover`"), which migrated `st.popover` to
`@floating-ui/react`.

- The popover body is portalled to `document.body` with
  `zIndex: theme.zIndices.popup !important` —
  `frontend/lib/src/components/elements/Popover/styled-components.ts`
  (`StyledPopoverBody`, via `getOverlayZIndex` in
  `frontend/lib/src/components/shared/Base/styled-components.ts`).
- `st.multiselect` still uses BaseWeb; BaseWeb overlays render in the shared
  "BaseWeb layer host" created in `frontend/lib/src/components/core/.../RootStyleProvider.tsx`
  (`position: fixed`), which is also pinned to `theme.zIndices.popup`.
- Same z-index → stacking falls back to DOM order. The BaseWeb layer host mounts
  at app startup (early); the popover's `FloatingPortal` is appended when the
  popover opens (later), so the popover body paints over the dropdown.

Before #15339, `st.popover` was itself a BaseWeb overlay in the same layer host,
so a later-opened dropdown naturally stacked above it — hence the regression.
Likely also affects other still-on-BaseWeb overlays inside a popover
(e.g. `st.date_input` / `st.time_input`); already-migrated widgets like
`st.selectbox` are appended after the popover and render correctly.

## Classification

- **Type:** Bug — z-index / stacking regression
- **Status:** Confirmed on 1.59.0, 1.59.1, and 1.59.2 (reported on 1.59.2)
- **Areas:** frontend — `Popover` (floating-ui) vs BaseWeb overlay layer host
  (`st.multiselect`)
- **Priority:** Medium — common pattern (filter widgets inside a popover) and the
  dropdown is unusable, but a single-select `st.selectbox` sidesteps it.
- **Fix complexity:** Small–Medium — give the popover body and the BaseWeb layer
  host distinct, well-ordered z-indices (or raise BaseWeb overlays above the
  popup layer), so a dropdown opened inside a popover always stacks above the
  popover body. Must be validated against other overlay combinations (tooltips,
  date/time inputs, nested popovers) to avoid regressing those.
