# Issue #16005 — Widgets in an st.popover opened inside an st.dialog are occluded and unusable

**Status:** Bug confirmed — regression
**Priority:** P2
**Type:** Regression
**Areas:** `st.popover`, `st.dialog`, frontend, react-aria

---

## Summary

Since 1.59.0, a `st.popover` opened **inside** a `st.dialog` has its body occluded by
the dialog's overlay. The popover paints but its widgets (e.g. a `selectbox`) are not
interactive: hit-testing the in-popover widget resolves to the dialog, the dropdown
cannot be opened, and clicking the widget lands on the dialog's dismiss overlay — which
can close the dialog. This regressed with the React Aria migration of `st.dialog`
(PR #15327, shipped in 1.59.0); it worked in 1.58.0.

## Finding

**Bug confirmed.** Independently reproduced on **1.59.0** (broken) and confirmed
**1.58.0** works, using Playwright against PyPI wheels in throwaway `uv venv`
environments. The reporter's `git bisect` (in the issue) identifies PR #15327 as the
first bad commit and confirms `develop` is still broken.

## Reproduction

Minimal app (reporter's snippet):

```python
import streamlit as st

@st.dialog("My dialog")
def show_dialog():
    st.write("dialog content")
    with st.popover("Open popover"):
        fruit = st.selectbox("Fruit", ["Apple", "Banana", "Cherry"])
        st.write(f"picked: {fruit}")

if st.button("Open dialog"):
    show_dialog()
```

**Objective evidence (Playwright, Chromium):** open the dialog, open the popover, then
hit-test the in-popover selectbox at its own center with `document.elementFromPoint`:

| Version | selectbox center hit-test | dropdown opens? | dialog stays open? | Result |
|---------|---------------------------|-----------------|--------------------|--------|
| 1.58.0  | `stSelectbox` (`inBody: true`) | yes | yes | **PASS** |
| 1.59.0  | `stDialog` (`inBody: false, inDialog: true`) | no | **no — click dismissed the dialog** | **FAIL** |

`document.elementsFromPoint` at the selectbox center on 1.59.0 returns only
`[stDialog, HTML]` — the popover body is absent from the hit-test stack entirely.

## Control cases (both PASS on 1.59.0)

Only the popover-in-dialog combination is broken:

| Control | Result on 1.59.0 |
|---------|------------------|
| Standalone popover (no dialog) — selectbox usable | PASS (hit-tests to `stSelectbox`) |
| Widget placed **directly** in the dialog (`multiselect`) — opens above dialog | PASS (options visible above dialog) |

## Version bracket

| Version | Status  | Notes |
|---------|---------|-------|
| 1.58.0  | Working | Pre–React Aria dialog (BaseWeb) |
| 1.59.0  | Broken  | React Aria `st.dialog` migration (PR #15327 — first bad commit) |
| develop | Broken  | Per reporter's bisect; `modal`-tier fix (#15876) does not cover this case |

## Root Cause

Both overlays are portalled to `document.body` and compete in the root stacking
context:

- **Dialog overlay** — `stDialog` is the React Aria `ModalOverlay`
  (`frontend/lib/src/components/shared/Modal/Modal.tsx` →
  `StyledDialogOverlay` in `.../Modal/styled-components.ts`), a full-viewport
  `position: fixed; inset: 0; pointer-events: auto` element that also serves as the
  dismiss layer.
- **Popover body** — `stPopoverBody` is portalled via `FloatingPortal` to
  `document.body` (`frontend/lib/src/components/elements/Popover/Popover.tsx`) at the
  `popup` z-index tier via `getOverlayZIndex`
  (`.../components/shared/Base/styled-components.ts`).

On **1.59.0** the dialog overlay computes to `z-index: 1000060` — the **`popup`**
tier, the *same* tier as the popover body. Tied at `popup`, the full-viewport dialog
overlay wins the hit-test over the popover body, so the in-popover widget is unusable
and clicks route to the dialog's dismiss overlay.

The z-index tiers are defined in
`frontend/lib/src/theme/primitives/zIndices.ts`:

```
modal          = popup - 1   // 1000059  (React Aria dialog surface — intended)
popup          = ...         // 1000060  (floating-ui popover body)
basewebOverlay = popup + 1   // 1000061  (BaseWeb dropdowns/calendars)
```

Widgets placed **directly** in a dialog work because their BaseWeb overlays render in
the higher `basewebOverlay` tier (`popup + 1`, hosted by `RootStyleProvider.tsx`),
which clears the dialog. The popover body sits at `popup` and does not.

**Note on the `modal` tier and #15876.** PR #15876 ("Fix React Aria dialog overlay
stacking") introduced `modal = popup - 1` to place the dialog *below* the `popup` tier
so nested overlays render above it, but that landed after 1.59.0 (the version tested
here still computes the dialog at `popup`). Even so, the reporter's bisect shows
`develop` remains broken for popover-in-dialog — so lowering the dialog tier for
BaseWeb/dataframe overlays did not resolve the floating-ui popover-body case. This is
consistent with #15876's scope (its e2e coverage is date input / selectbox /
multiselect / dataframe column menu in a dialog — no popover-in-dialog test).

### Suggested fix direction

Mirror how direct BaseWeb overlays clear the dialog: either

1. **Raise the popover body above the dialog overlay** when it is opened inside a
   dialog (e.g. give the popover body a tier at or above `basewebOverlay`, or portal
   it into the BaseWeb layer host / dialog overlay context), or
2. **Portal the popover body into the dialog's overlay/stacking context** so it
   participates in the same layer as the dialog rather than the root `popup` tier.

Add an e2e regression test for popover-in-dialog (the existing dialog e2e coverage
does not include it).

## Classification

- **Type:** `type:bug`, `type:regression`
- **Introduced:** PR #15327 (React Aria `st.dialog` migration, 1.59.0)
- **Areas:** `feature:st.popover`, `feature:st.dialog`, frontend, react-aria
- **Fix complexity:** Small–Medium — a z-tier/portal adjustment on the popover body plus
  an e2e regression test; needs care not to reintroduce dialog dismissal on interaction.
- **Workaround:** None for the popover-in-dialog pattern. Place interactive widgets
  directly in the dialog, or keep the popover outside the dialog.

## Priority Recommendation: P2

Per `wiki/issue-prioritization.md`, reach is measured by **who hits and notices the
broken behavior, not who uses the affected surface**, and regressions bias upward.

- It is a **regression** with **no workaround** for the affected pattern, and the
  failure is severe when hit (the in-popover widget is completely unusable, and
  interacting with it can dismiss the whole dialog).
- However, it only triggers for the **specific combination of a popover nested inside a
  dialog** — narrower than a bare popover or a bare widget-in-dialog. Standalone
  popovers and widgets placed directly in a dialog both work.
- This calibrates against the "overlay behind a container" family: `st.selectbox`
  dropdown behind `st.dialog` (#15599) is **P2** and `st.date_input` calendar behind
  `st.dialog` (#15859) is **P1** for a common single-widget-in-dialog case. The nested
  popover-in-dialog pattern here is less common than either, which keeps it below the
  P1 ">5% of users will notice" bar despite the high per-instance severity.

Lands at **P2** ("a less noticeable regression … or confusing behavior", regression
with a straightforward low-risk fix). Could rise to P1 if it accrues meaningful
👍/comments or if popover-in-dialog proves more common than assumed.
