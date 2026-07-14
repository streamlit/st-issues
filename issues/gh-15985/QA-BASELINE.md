# gh-15985 QA baseline: `st.selectbox` type-to-search behavior in 1.58.0

This document captures the **expected `st.selectbox` typing/search behavior as it
was in Streamlit 1.58.0** — the last release before the regression in #15985.
Use it as the QA acceptance baseline for the fix (PR
[#15996](https://github.com/streamlit/streamlit/pull/15996)): the fixed build
should reproduce this behavior.

All behavior below was **empirically verified** by running Streamlit `1.58.0` in
an isolated venv and driving it with Playwright, not just read from source.

## Why 1.58.0 is the baseline

The bug is a regression introduced in **1.59.0** by the react-aria rewrite
(#15438, "Remove BaseWeb for selectbox"). In 1.59.x the committed label lives
*inside* the text input with the caret at the end, so the first keystroke
**appends** (`Banana` + `ch` → `Bananach`) and the fuzzy filter matches nothing.
1.58.0 is the last version with the correct behavior, so it defines the target.

## Mental model (1.58.0 / BaseWeb `Select`)

- The selectbox is a BaseWeb `Select` (single, searchable combobox).
- A committed value renders as a **separate value label** in the value
  container; the underlying `<input>` value is `""`.
- The moment you type, the committed label is **visually hidden** and the input
  holds *only what you typed* — the search query always starts empty.
- Filtering is **fuzzy by default** (`fzy`), **case-insensitive**, and matches
  against the option **label only**, sorted by descending fuzzy score.
- Escape / blur without an explicit selection **restores** the committed value.

## Expected behavior — verified step by step

### 1. Core path (the fix target)
Pre-selected `Banana` (index=2), focus, type `ch`:

| Step | input value | value label | dropdown |
|------|-------------|-------------|----------|
| Initial | `""` | `Banana` | — |
| After focus/click | `""` | `Banana` | all 10 options |
| After typing `ch` | `ch` (NOT `Bananach`) | *hidden* | `['Cherry', 'Peach']` |
| After Enter | `""` | `Cherry` | closed |

This is the single most important thing to replicate.

### 2. Opening the dropdown shows ALL options
Focus/click (or click the chevron) opens the full, unfiltered list of all
options. It is **not** pre-filtered by the current value.

### 3. Fuzzy matching specifics
- Non-contiguous match: `ape` → `['Grape', 'Apple']` (letters in order, not a substring).
- Case-insensitive: `CHER` → `['Cherry']`.
- Score ordering: `p` → `['Pear', 'Peach', 'Apple', 'Grape', 'Apricot']` (best score first).
- Matches the **label** only.

### 4. Enter commits the highlighted option
- With a filtered list open, `Enter` commits the currently **highlighted** option.
- Arrow keys move the highlight: type `a` (highlight `Apple`), `ArrowDown` →
  `Apricot`, `Enter` → commits `Apricot`.
- Legacy quirk: the default highlight after filtering isn't always the visual
  top row (query `p` committed `Apple`, the 3rd row). Treat "Enter commits the
  highlighted match" as the contract; do not fail the fix on matching this exact
  BaseWeb idiosyncrasy.

### 5. No-match query does not commit
Type `xyz` / `zzz` → dropdown empty, input keeps the typed text, value label
hidden. Pressing `Enter` on a no-match query does **nothing** (no commit).

### 6. Escape restores the committed value
After typing a query (matching or not), `Escape` discards the query, closes the
dropdown, and restores the committed label (input back to `""`).

### 7. Blur (click away) restores the committed value
Focus, type `gr` (dropdown → `Grape`), click elsewhere without selecting → query
discarded, committed value restored, input back to `""`. Typing alone never
mutates the committed value; only an explicit selection does.

### 8. Backspace on a committed value = edit-in-place, not delete
- Committed `Cherry`, focus, press `Backspace` once → the label converts into
  **editable text minus the last char**: input becomes `Cherr`, label hidden,
  dropdown filters to `['Cherry']`.
- Blur/Escape at this point **restores** `Cherry` (pre-edit value is remembered).
- A single Backspace does not clear the whole selection.

### 9. Empty selection (`index=None`)
- Initial: input `""`, placeholder `Choose an option`.
- Focus → full list. Type `man` → `['Mango']`. Escape → back to placeholder
  (value stays `None`).

### 10. `accept_new_options=True`
- Pre-selected `Banana`, focus, type `Kiwi` (not in list) → dropdown shows an
  `Add: Kiwi` creation entry. `Enter` commits the new value (label → `Kiwi`).
- Same type-to-replace behavior applies while typing the new value.

## QA acceptance checklist for PR #15996

The fixed build should satisfy all of these (matching 1.58.0):

1. Committed value + focus + type → input contains **only typed chars** (no
   `Bananach` append). **[primary]**
2. While typing, the committed label is not shown concatenated with the query.
3. Opening the dropdown shows the **full** option list, not a pre-filtered one.
4. Fuzzy, case-insensitive, label-only matching with score ordering
   (`ape`→Grape/Apple; `CHER`→Cherry).
5. `Enter` commits the highlighted option; arrow keys move the highlight first.
6. No-match query: empty dropdown, `Enter` does not commit.
7. `Escape` discards the query and restores the committed value.
8. Blur without selection restores the committed value.
9. Single `Backspace` on a committed value enters edit-in-place; blur/Escape
   restores the original.
10. `index=None` and `accept_new_options=True` variants all follow the same
    type-to-replace search behavior.

Cross-browser note: verify in **both Chromium and WebKit**. The PR explicitly
avoids a focus-time `select()` approach because WebKit/Safari collapses the
selection on mouse-up (keystroke still appends); item 1 must hold in WebKit too.
