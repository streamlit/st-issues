# gh-15941: pydeck selection events dropped inside st.fragment

## Summary

Reporter says `st.pydeck_chart(..., on_select="rerun", key=...)` silently drops
click/selection events when the chart is rendered inside `@st.fragment`, while
the identical chart outside a fragment works and hover picking/tooltips keep
working. Flagged as a regression on 1.56.0 and 1.59.1.

## Finding

**Cannot reproduce in a clean environment.** On macOS with the released
`streamlit==1.59.1` (pydeck 0.9.3, Python 3.13, headless Chromium), the
in-fragment selection was delivered correctly in every sequence tested. Also
verified on the current dev build (1.58.0).

## Reproduction

Tested in an isolated venv with the released 1.59.1 wheel (the exact version the
reporter used), driving the app with Playwright. Ran both a deterministic config
(SF hexes with known pixel coords) and the reporter's **verbatim** code (São
Paulo hexes, `map_style=None`, default `selection_mode`, shared `id="hexes"`).

| Sequence | in-fragment result |
|---|---|
| click outside chart, then inside chart | `SELECTED_OK` ✅ |
| click only the inside chart (fresh page) | `SELECTED_OK` ✅ |
| rapid successive clicks on both charts | both `SELECTED_OK` ✅ |
| verbatim repro, inside chart only | `SELECTED_OK` ✅ |

In all cases `event.selection.objects` was populated and the fragment reran; the
outside chart correctly stayed unselected when only the inside chart was clicked.

## Root Cause

Unknown — not reproduced. The frontend click path is
`handleClick` (`frontend/lib/src/components/elements/DeckGlJsonChart`) →
`setSelection` → `useBasicWidgetClientState` →
`widgetMgr.setStringValue(..., { fromUi: true }, fragmentId)` →
`WidgetStateManager.scheduleFlush(fragmentId)` → `sendUpdateWidgetsMessage`.

The triage comment hypothesized that `scheduleFlush`
(`frontend/lib/src/WidgetStateManager.ts`) mishandles a batch mixing `undefined`
(outside-fragment) and defined (inside-fragment) `fragmentId`s. That batching
only coalesces updates fired within the **same** macrotask (a single
`setTimeout(0)`); normal user clicks separated by pydeck's ~200ms selection
debounce never land in the same tick, so this path isn't exercised in practice.
The mixed-`fragmentId` guard (`hasFragmentIdConflict`) has also existed since
2025-10-24 (#12747), predating the reported regression window.

Most likely environment- or hardware-specific: reporter is on Windows 11 /
Docker Debian, Python 3.14/3.11, real Chrome. A software (SwiftShader) vs.
hardware WebGL context, or an interaction not present in the minimal repro, are
plausible causes. This app is published so it can be tried on the affected
machines and the click event inspected (does an `updateWidgets`/rerun BackMsg go
out over the websocket on the in-fragment click?).

## Classification

- **Type:** Bug (reported); currently unconfirmed
- **Status:** Cannot reproduce on 1.59.1 (incl. verbatim repro) or 1.58.0 dev
- **Areas:** frontend, `st.pydeck_chart` (DeckGlJsonChart) / event handling / `st.fragment`
- **Priority:** Low–Medium — no clean-env reproduction; suspected environment-specific
- **Fix complexity:** Unknown — needs a reproduction first (browser console/network + `chrome://gpu` from the reporter)
