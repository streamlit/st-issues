# gh-15985: Typing into the selectbox doesn't search anymore

## Summary

With a value already committed in an `st.selectbox`, focusing the widget and
typing no longer clears the label to start a fresh search. Instead the typed
characters are appended behind the committed label (select "Banana", type "ch"
→ `Bananach`), so the fuzzy filter matches nothing. Confirmed as a regression
introduced in 1.59.0.

## Finding

**Bug confirmed on 1.59.0.** Reproduced with Playwright against a released
Streamlit 1.59.0 build: the input value went from `Banana` to `Bananach` after
typing `ch`, and the dropdown showed "No results". Expected behavior is for the
input to clear to `ch` and filter to "Cherry".

## Reproduction

- **Version tested:** 1.59.0 (released), served locally via `streamlit run`.
- **Method:** self-contained Playwright script — select the default value, click
  the input, type `ch`, read the input value.
- **Observation:**

  | Step | Input value |
  |------|-------------|
  | Initial selection | `Banana` |
  | After typing `ch` | `Bananach` (bug) — expected `ch` |

  The dropdown then renders "No results" because `Bananach` matches no option.

## Root Cause

The reporter attributes the regression to
[#15870](https://github.com/streamlit/streamlit/pull/15870) ("Virtualize
selectbox dropdown option list"), but that PR only rewrote the dropdown's option
rendering and — per `git merge-base --is-ancestor` — is **not** in stable
1.59.0/1.59.1/1.59.2 (it exists only in dev builds). It cannot be the cause of a
bug seen on stable 1.59.2.

The actual regression is
[#15438](https://github.com/streamlit/streamlit/pull/15438) ("Remove BaseWeb for
selectbox"), the react-aria-components rewrite that first shipped in **1.59.0**
(verified: in `1.59.0`, not in `1.58.0`). This matches the reporter's "since
1.59.0".

In the rewritten component
(`frontend/lib/src/components/shared/Dropdown/Selectbox.tsx`), the input is a
controlled react-aria `ComboBox` whose `inputValue` is initialized/kept as the
committed label (`propValue`). On focus the committed label stays in the input
and the caret sits at the end, so the first keystroke is handled by
`handleInputChange` as *append* (`Banana` + `ch`), which sets `filterActive` and
runs the fuzzy filter against `Bananach` — matching nothing. There is no
focus-time behavior that clears the query or selects the existing text. The old
BaseWeb selectbox cleared the search query when the user began typing, which is
the behavior users expect.

## Suggested Fix Direction

Restore "type to replace" on focus. The most standard, low-risk approach is to
select all text in the input on focus (e.g. an `onFocus` handler that calls
`event.currentTarget.select()`), so the committed label stays visible but the
first keystroke replaces it and starts a fresh search. Alternatively, clear
`inputValue` on focus and rely on the existing `handleBlur` to restore the
committed value when the user tabs away without choosing. The select-all
approach is preferable because it keeps the current value visible while
signalling that typing will replace it.

## Classification

- **Type:** Bug — regression
- **Status:** Confirmed on 1.59.0 (introduced by #15438, the react-aria rewrite;
  NOT #15870 as the reporter guessed)
- **Areas:** frontend, `Selectbox` (`shared/Dropdown/Selectbox.tsx`)
- **Priority:** P1 — a regression in a core, non-experimental widget's common
  interaction (type-to-search in `st.selectbox`) that affects everyone with a
  pre-selected value; only a clunky, non-obvious workaround (manually clear the
  field first) exists.
- **Fix complexity:** Small — add focus-time select-all / clear handling to the
  ComboBox input; guard the existing blur-restore path.
