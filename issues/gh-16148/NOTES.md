# gh-16148: Fullscreen button has no element-specific accessible label

## Summary

The **Fullscreen** button rendered on `st.image` (and every other
fullscreen-capable element) always exposes the accessible name
`aria-label="Fullscreen"`. It never references the element it expands, so a
screen reader user navigating a page with multiple images/charts hears a list
of identical "Fullscreen button" controls with no way to distinguish them.

## Finding

**Bug confirmed on 1.57.0.** A minimal app with two captioned images renders
two Fullscreen buttons that both have `aria-label="Fullscreen"`, regardless of
the caption ("Federal Command Center" vs. "DoD Network Architecture"). The
label is a hard-coded frontend constant, so the same behavior is present on
`develop`. This is **not a regression** — the button has been labelled this way
since the element toolbar was introduced.

## Reproduction

- **Version tested:** released wheel `streamlit==1.57.0`.
- **Method:** Playwright — hover each `stFullScreenFrame`, read the Fullscreen
  button's `aria-label`.
- **Observed:**

  | Image caption             | Fullscreen button `aria-label` |
  | ------------------------- | ------------------------------ |
  | Federal Command Center    | `Fullscreen`                   |
  | DoD Network Architecture  | `Fullscreen`                   |

  Expected at least the caption to be part of the accessible name (e.g.
  `"Federal Command Center Fullscreen"`). Screenshot: `repro_gh_16148.png`.

## Root Cause

`Toolbar` renders the fullscreen action with a static label:

- `frontend/lib/src/components/shared/Toolbar/Toolbar.tsx:127-133` —
  `<ToolbarAction label="Fullscreen" ... />` (and `label="Close fullscreen"`
  for the exit button at `:134-140`).
- `ToolbarAction` maps that `label` straight onto the button:
  `aria-label={label}` at `Toolbar.tsx:79`.

No element-specific context is plumbed through. Callers like
`ImageList` already have the caption in scope
(`frontend/lib/src/components/elements/ImageList/ImageList.tsx:135-138`) but do
not pass it to `<Toolbar onExpand={expand} ... />`
(`ImageList.tsx:212-218`). Other callers (DataFrame, PlotlyChart,
DeckGlJsonChart, AudioInput, MermaidChart) render the same toolbar and share
the issue.

## Fix Direction

Give the fullscreen button an element-specific accessible name while keeping
the visible tooltip short:

- Add an optional label/aria-label prop on `Toolbar` / `ToolbarAction` (e.g.
  an `ariaLabel` distinct from the tooltip `label`), and set it to something
  like `"Fullscreen: {caption}"` when a caption/title is available.
- Plumb the caption from `ImageList` (and, where a natural title exists, the
  other toolbar callers) into `Toolbar`.
- Keep the visible tooltip as "Fullscreen"; only the accessible name needs the
  element context. Fall back to plain "Fullscreen" when no label is available
  so nothing regresses.

## Classification

- **Type:** Bug (accessibility) — arguably an enhancement, but identical,
  context-free control names are a real WCAG usability problem.
- **Status:** Confirmed on 1.57.0; present on `develop` (frontend constant).
- **Areas:** frontend — `shared/Toolbar`, consumed via `ElementFullscreen` /
  `withFullScreenWrapper` by ImageList, DataFrame, PlotlyChart,
  DeckGlJsonChart, AudioInput, MermaidChart.
- **Priority:** **P3** — genuine accessibility defect affecting screen-reader
  users across all fullscreen-capable elements, but each button *is* labelled
  (just not uniquely), the impact is limited to distinguishing multiple
  controls on one page, and an author-side workaround exists. Could be raised
  to P2 given Streamlit's accessibility commitments. (Note:
  `wiki/issue-prioritization.md` was not available locally; this follows the
  standard P0–P4 criteria — reach measured by the broken behavior, not the
  affected surface.)
- **Fix complexity:** Small–Medium — thread an optional accessible label
  through `Toolbar`/`ToolbarAction` and populate it from callers that have a
  caption/title; update snapshot/DOM tests.
