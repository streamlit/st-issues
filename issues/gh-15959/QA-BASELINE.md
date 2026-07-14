# gh-15959 QA baseline: overlays inside `st.popover` in 1.58.0

This document captures the **expected behavior of BaseWeb overlays inside an
`st.popover` as it was in Streamlit 1.58.0** — the last release before the
regressions in #15959. Use it as the QA acceptance baseline for the fix (PR
[#15961](https://github.com/streamlit/streamlit/pull/15961)): the fixed build
should reproduce this behavior.

All behavior below was **empirically verified** by running Streamlit `1.58.0` in
an isolated venv and driving it with Playwright (hit-testing with
`document.elementFromPoint` and checking popover visibility after each
interaction), not just read from source.

## Why 1.58.0 is the baseline

PR #15961 fixes two related regressions introduced in **1.59.0** by the
`st.popover` migration to floating-ui (#15339, "Remove BaseWeb for Popover").
After that migration the popover no longer participates in BaseWeb's layer
stack, which broke:

1. **Stacking (#15959):** BaseWeb overlays (multiselect/date/time dropdowns)
   opened inside a popover rendered *behind* the popover body (same `popup`
   z-index → DOM order wins → popover body paints on top).
2. **Dismissal:** interacting with an overlay inside a popover could dismiss the
   popover (close-on-select overlays detach the clicked node before the
   document click handler runs, so it's misclassified as an outside click).

1.58.0 (BaseWeb popover, pre-migration) is the last version where both worked
correctly, so it defines the target.

## What the fix changes (areas to QA)

- **z-index tiers:** new `basewebOverlay` tier (`popup + 1`) for the BaseWeb
  layer host so dropdowns/calendars paint above the popover body (`popup`);
  **toast** moves to `popup + 2` (stays above overlays); `tablePortal`
  (dataframe overlays) stays above everything.
- **Dismissal:** outside-click handling records the interaction origin on
  capture-phase `pointerdown` and Enter/Space `keydown`, and treats the trigger,
  popover body, and any `data-st-overlay-root` surface as "inside."

## Expected behavior — verified in 1.58.0

### A. Stacking — overlays render ABOVE the popover body
For each widget, open the popover, open the widget's overlay, and hit-test the
center of an option/day. In 1.58.0 the topmost element is the option/day itself
(not the popover body):

| Widget in popover | Overlay | Hit-test at option center | Result |
|---|---|---|---|
| `st.multiselect` | options dropdown | option DIV, **not** inside popover body | ABOVE ✅ |
| `st.selectbox` | options dropdown | option DIV, **not** inside popover body | ABOVE ✅ |
| `st.date_input` | calendar | day cell (`July 15`), **not** inside popover body | ABOVE ✅ |
| `st.time_input` | time dropdown | option (e.g. `00:30`) clickable and commits | ABOVE ✅ |
| nested inner `st.popover` → `st.selectbox` | options dropdown | option DIV, **not** inside popover body | ABOVE ✅ |

### B. Dismissal — interacting with an inner overlay KEEPS the popover open
Selecting from the overlay commits the value **and the popover stays open**:

| Scenario | After selecting from the inner overlay |
|---|---|
| `st.multiselect` — pick an option | popover stays open, value committed |
| `st.selectbox` — pick an option (single-select, closes on select) | popover stays open, value = `Cherry` |
| `st.date_input` — pick a day | popover stays open, value = `2026-07-15` |
| `st.time_input` — pick a time | popover stays open, value = `00:30:00` |
| **nested popovers** — open outer, open inner, pick from inner widget | **both** outer and inner stay open, value = `Grape` |
| **popover in `st.dialog`** — pick from popover's selectbox | dialog and popover both stay open, value = `Apple` |

### C. Normal dismissal still works
| Action | Result |
|---|---|
| Click truly outside (page background) | popover dismisses ✅ |
| Press `Escape` | popover dismisses ✅ |

### D. Toast stacking (verify — not part of the empirical run)
The fix moves `toast` to `popup + 2` so notifications stay above an open BaseWeb
overlay. Expected: a toast shown while a dropdown/calendar inside a popover is
open renders **above** that overlay. (This edge case was not measured on 1.58.0;
treat it as a "should hold" item and verify on the fixed build.)

## QA acceptance checklist for PR #15961

The fixed build should satisfy all of these (matching 1.58.0):

**Stacking**
1. `st.multiselect` dropdown inside a popover renders **above** the popover body
   (options are hit-testable and clickable). **[primary — the #15959 report]**
2. `st.date_input` calendar inside a popover renders above the popover body.
3. `st.time_input` dropdown inside a popover renders above the popover body.
4. `st.selectbox` dropdown inside a popover renders above the popover body.
5. `tablePortal` (dataframe) overlays still render above popover overlays; toast
   still renders above open BaseWeb overlays.

**Dismissal**
6. Selecting a `multiselect` option inside a popover does **not** dismiss it.
7. Selecting a `selectbox` option (closes-on-select) does **not** dismiss the
   popover. **[primary — the close-on-select detach case]**
8. Picking a `date_input` day does **not** dismiss the popover.
9. Picking a `time_input` value does **not** dismiss the popover.
10. Nested popovers: interacting with the inner popover's widget does **not**
    dismiss the outer popover.
11. Popover inside `st.dialog`: interacting with the popover's widget dismisses
    neither the popover nor the dialog.

**Regression guards (must still work)**
12. Clicking truly outside the popover dismisses it.
13. `Escape` dismisses the popover (and closes an inner overlay first if one is
    open, before closing the popover).
14. Re-opening a popover after dismissal works (no stale "interaction inside"
    state suppressing the next outside click — the PR resets this on open).

## Notes for the tester

- Use `document.elementFromPoint` hit-testing at the center of an option/day to
  verify stacking objectively (topmost element should be the option, with no
  `[data-testid="stPopoverBody"]` ancestor), as in
  `st_popover_test.py::test_multiselect_dropdown_renders_above_popover_body`.
- The BaseWeb date picker needs the input activated before the calendar mounts;
  in an automated harness a stray transparent `div` can intercept the first
  click, so click/activate deliberately before locating day cells.
- Verify in both Chromium and WebKit.
