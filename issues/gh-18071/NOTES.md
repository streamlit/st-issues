# gh-18071: NumberColumn silently drops rejected characters

## Summary

Typing a character that the `st.data_editor` `NumberColumn` editor does not accept
(e.g. `,` when the browser locale uses `.` as the decimal separator, or a letter)
silently removes it while typing, and the resulting different number is committed
as a normal edit. `1,23` commits `123.0`; `1a2` commits `12.0`.

## Finding

**Bug confirmed** on 1.67.0 (latest release) and 1.52.2 (reported). Also present on
1.30.0, so this is **long-standing behavior, not a regression** (the reporter ticked
"regression" but only tested versions that have the bug). `develop` is unchanged in
this code path since 1.67.0 (no changes to the Glide patch, `NumberColumn.ts`, or the
Glide / `react-number-format` versions), so it is affected too.

## Reproduction

Released wheels in throwaway venvs, driven by Playwright (system Chrome, `en-US`
locale). The editor is opened with Enter first, then the text is typed.

| Version | `1,23` editor shows → commits | `1.23` | `1a2` |
|---------|-------------------------------|--------|-------|
| 1.67.0  | `123` → `123.0`               | `1.23` | `2`/`12` → `2.0`/`12.0` |
| 1.52.2  | `123` → `123.0`               | `1.23` | `12` → `12.0` |
| 1.30.0  | `123` → `123.0`               | `1.23` | `12` → `12.0` |

No invalid-cell styling or message is shown at any point. Screenshots:
`v1.67.0_typing_comma.png`, `v1.67.0_after_commit.png`, `app_after_edits.png`.

Side observation: with `format="plain"` the committed `123.0` renders as
`123.00000000000001` in the grid (separate float-display issue, not investigated).

Note on the verification script: typing straight onto a selected cell (no Enter
first) also drops the `.` in `1.23`, because the first keystroke opens the overlay
and the next ones arrive before the input is focused. The script opens the editor
first to avoid this artifact.

## Root Cause

Glide's number overlay editor renders `react-number-format`'s `NumericFormat`
(`@glideapps/glide-data-grid/.../number-overlay-editor.js`). `NumericFormat` strips
every character except digits, `-` (when `allowNegative`), the decimal separator
(taken from `Intl.NumberFormat()` — the browser locale), and the thousand separator.
`frontend/lib/src/components/widgets/DataFrame/columns/NumberColumn.ts:169` passes
`thousandSeparator: ""`, so in an English browser `,` is not accepted and is dropped
on keystroke. `onValueChange` then emits the already-parsed float (`123`), so
Streamlit's `validateInput` (`NumberColumn.ts:172`) only ever sees a valid number and
has nothing to flag.

The leading-`.` fix for #16909 (#16920) patched the same overlay
(`frontend/.yarn/patches/@glideapps-glide-data-grid-npm-6.0.4-alpha24-9c1a40557b.patch`)
to keep the typed text, but it does not stop `NumericFormat` from discarding
characters.

Fix direction: in the same patch, stop `NumericFormat` from silently filtering
(e.g. keep the raw input string and mark the cell invalid when it doesn't parse), or
at minimum accept both `,` and `.` as decimal separators
(`allowedDecimalSeparators` in `react-number-format`) for the common locale case.

## Workaround

`TextColumn` with `validate=r"^-?\d+([.,]\d+)?$"`, converting to a number in Python
(replace `,` with `.`, then `pd.to_numeric`). Invalid text stays visible and is
highlighted. Loses numeric sorting and right alignment. Implemented as live widgets
in `app.py` and **verified on 1.67.0** with `verify_workaround_gh_18071.py`: typing
`1,23` and `1.23` both convert to `1.23`, while the bug demo in the same app returns
`[123.0, 1.23]`.

## Classification

- **Type:** Bug
- **Status:** Confirmed on 1.67.0, 1.52.2, 1.30.0; `develop` unchanged
- **Areas:** frontend, `st.data_editor` / `NumberColumn` (Glide number overlay editor)
- **Priority:** P2 — like #16909 (rated P2), it silently commits a plausible but
  incorrect number in a core editing workflow, and users in comma-decimal locales hit
  it by habit; a workaround exists (`TextColumn` + validate), but users who hit the
  bug usually don't notice the corruption.
- **Fix complexity:** Medium — needs a change to the patched Glide number overlay
  (keep raw text and surface invalid state), plus deciding how to treat `,` vs `.`
  without conflicting with the localization enhancement (#11164).
