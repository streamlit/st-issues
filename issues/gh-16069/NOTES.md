# gh-16069: selectbox in a popover is slow with many options

## Summary

A `st.selectbox` with many options (`range(10000)`) inside `st.popover` is slow
to open, and the delay grows with the option count and is paid again on every
reopen. **Confirmed** as a genuine performance regression on 1.59.2 vs. 1.58.0:
popover-open latency scales linearly with the selectbox's option count on 1.59.x
but was near-constant on 1.58.0.

## Finding

**Bug confirmed.** The general large-options slowdown the reporter mentions was
addressed for top-level selectboxes, but the *popover* case remains slow because
of how popovers mount their contents (see Root Cause). Verified with Playwright
against released wheels 1.58.0 (good) and 1.59.2 (regressed), bracketing the
1.59 React Aria migration.

## Reproduction

Minimal app (`repro_gh_16069.py`): a top-level selectbox and a popover
selectbox, both with `range(10000)`. The Playwright script (`verify_gh_16069.py`)
measures, per version:

- time to open the **top-level** selectbox's option list (baseline), and
- time to **open the popover** and then open the in-popover selectbox's list,
  repeated over 5 open/close cycles.

Because this machine is much faster than the reporter's (Windows 11 / Firefox),
runs are repeated under 6× CDP CPU throttling to make the regression legible.
Timings are wall-clock ms; the meaningful signal is the **relative** difference
between versions and the **scaling with option count**, not absolute numbers.

### Popover-open latency, N = 10,000 options

| Version | Unthrottled | 6× CPU throttle |
|---------|-------------|-----------------|
| 1.58.0  | ~25 ms      | ~61 ms          |
| 1.59.2  | ~93 ms      | ~350 ms         |

→ ~3.7× slower unthrottled, ~5.7× slower throttled. The top-level selectbox is
fine on both versions; only the popover-open path regressed.

### Popover-open latency scales with option count (1.59.2, 6× throttle)

| Options (N) | Popover open (avg) |
|-------------|--------------------|
| 10          | ~62 ms             |
| 10,000      | ~350 ms            |
| 50,000      | ~1,527 ms          |

The cost is essentially constant across all 5 reopens at each N (e.g. ~1,520 ms
every time at N=50,000), confirming the full collection is rebuilt on **every**
open rather than cached.

### Not a DOM-size problem

Both the top-level and in-popover option lists are virtualized — only ~11
`[role="option"]` nodes render regardless of N. The cost is in building the
React Aria collection at mount, not in rendering DOM nodes.

## Root Cause

Two behaviors compound:

1. **`st.popover` unmounts its body when closed and re-mounts on open.** The
   popover body (and everything inside it, including the selectbox) is
   conditionally rendered only while open:
   `frontend/lib/src/components/elements/Popover/Popover.tsx:352`
   (`{open && (<FloatingPortal>…{children}…</FloatingPortal>)}`).

2. **The selectbox's React Aria `ComboBox` materializes its full option
   collection at mount.** All options are mapped into item objects
   (`frontend/lib/src/components/shared/Dropdown/Selectbox.tsx:273`) and passed
   to `<ComboBox … items={displayOptions}>`
   (`Selectbox.tsx:558`, list at `:622`). React Aria builds its internal
   `ListCollection` over all N items when the ComboBox renders, independent of
   whether the dropdown is open (the *rendering* is virtualized, but collection
   construction is O(N)).

Together: each popover open re-mounts the selectbox and rebuilds the entire
N-item collection, so popover-open latency is O(number of options) and is
re-paid on every open. A top-level selectbox mounts once on page load, so it
pays this cost a single time — which is why the earlier fix for the general
large-options slowdown doesn't help the popover case.

This is a regression from the 1.59 React Aria selectbox migration (the BaseWeb
dropdown used previously deferred list construction until the dropdown actually
opened, so popover open was cheap regardless of option count — 1.58.0 popover
open is ~25 ms even with 10,000 options).

### Fix direction

Avoid rebuilding the full collection on every popover mount. Options to explore:
- Keep popover contents mounted (render hidden) instead of unmounting on close,
  so the selectbox collection persists across opens — this changes popover
  semantics and may have side effects, so weigh carefully.
- Reduce the per-mount cost of building the React Aria collection for large
  option counts (e.g. lazy/deferred collection construction, or a lighter
  collection representation), so remount is cheap.

## Classification

- **Type:** Bug — performance regression
- **Status:** Confirmed on 1.59.2; not present on 1.58.0
- **Areas:** frontend — `shared/Dropdown/Selectbox` (React Aria ComboBox) +
  `elements/Popover`
- **Priority:** **P2** — Regression with no functional data loss (the widget
  works, it's just laggy) and a clear workaround (keep large selectboxes out of
  popovers / reduce option count). Reach is limited to the specific combination
  of a popover containing a large-option selectbox, but the degradation is
  severe at high option counts (~1.5 s per open at 50k, worse on the reporter's
  slower hardware) and re-paid on every open. Consistent with the P2 rating
  given to the sibling 1.59 selectbox regressions (#16003, #16004, #16005).
  *(Note: `wiki/issue-prioritization.md` was not available in this environment;
  this recommendation follows the standard regression/reach/severity/workaround
  criteria and the calibration of adjacent issues.)*
- **Fix complexity:** Medium — touches popover mount lifecycle and/or React Aria
  collection construction; needs care to avoid regressing popover dismissal and
  selectbox state behavior.
