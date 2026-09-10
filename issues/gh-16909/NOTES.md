# gh-16909: Typed leading decimal is dropped in `NumberColumn`

## Summary

Typing a leading-decimal value such as `.07` into an editable numeric cell drops
the decimal point and commits `7.0000`. The bug was reproduced with literal,
sequential keystrokes on both the originally reported Streamlit 1.61.1 and the
latest stable PyPI release, Streamlit 1.63.0.

## Finding

**Bug confirmed on the reported version and still present in the latest stable
release.** On both Streamlit 1.61.1 and 1.63.0, after `.07` was typed, the open
input contained `7`, and pressing Enter made the app render
`Committed margin: 7.0000` instead of `Committed margin: 0.0700`.

## Reproduction

- **Originally reported version:** Streamlit 1.61.1 release wheel
- **Latest stable version:** Streamlit 1.63.0 release wheel, determined from
  PyPI on 2026-09-10
- **Python:** 3.13 for both runs
- **Browser:** headless Chromium for both runs
- **Method:** The same Playwright verifier used three sequential keyboard
  events for `.`, `0`, and `7` in both runs.
- **Verification result on both versions:** the regression assertion failed as
  intended:

  ```text
  Leading-decimal entry was corrupted: input showed '7' after typing and
  the app rendered 'Committed margin: 7.0000'; expected
  'Committed margin: 0.0700'.
  ```

Typing a leading zero (`0.07`) or pasting the complete string (`.07`) avoids the
character-by-character failure.

## Root cause

Streamlit creates numeric cells as Glide Data Grid `GridCellKind.Number` cells
in
`frontend/lib/src/components/widgets/DataFrame/columns/NumberColumn.ts`.
`useCustomEditors` only supplies a custom editor for read-only JSON text cells,
so numeric cells use Glide's built-in number overlay.

Both Streamlit 1.61.1 and 1.63.0 use
`@glideapps/glide-data-grid@6.0.4-alpha24` with
`react-number-format@5.4.4`. That overlay is a controlled `NumericFormat`. It
reports `floatValue` after every keystroke, and Glide immediately replaces the
cell's numeric `data` with that value. A lone `.` has no numeric `floatValue`,
so the controlled rerender loses the decimal before the following digits
arrive. The subsequent `0` and `7` are therefore interpreted as the whole
number `7`.

This is distinct from Streamlit's parsing path:
`NumberColumn.getCell(".1312314")` already has unit coverage and correctly
produces `0.1312314`. Glide's paste handler also receives the complete string
and parses it with `Number.parseFloat`, which explains why pasting `.07` works.

Relevant code:

- `frontend/lib/src/components/widgets/DataFrame/columns/NumberColumn.ts:96-114`
- `frontend/lib/src/components/widgets/DataFrame/columns/NumberColumn.ts:162-180`
- `frontend/lib/src/components/widgets/DataFrame/hooks/useCustomEditors.ts:43-57`
- `frontend/lib/src/components/widgets/DataFrame/columns/NumberColumn.test.ts:149-168`
- `@glideapps/glide-data-grid/dist/esm/cells/number-cell.js`
- `@glideapps/glide-data-grid/dist/esm/internal/data-grid-overlay-editor/private/number-overlay-editor.js`

A fix needs to preserve incomplete in-progress text such as `.`, `.0`, or `-`
until it becomes a complete number, either through a Streamlit-provided numeric
editor or a patch/upstream change to Glide's overlay.

## Classification

- **Type:** Bug
- **Status:** Confirmed on reported version 1.61.1 and latest stable release
  1.63.0
- **Areas:** frontend, `st.data_editor`, `NumberColumn`
- **Priority:** P3 — the bug silently commits plausible but incorrect data and
  is worth fixing, but it requires a specific shorthand typing pattern and has
  straightforward leading-zero and paste workarounds.
- **Fix complexity:** Medium — preserve raw transient text in the controlled
  numeric overlay and add typed-entry regression coverage without changing
  valid number, formatting, paste, or IME behavior.
