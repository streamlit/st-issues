# gh-17112: Button dropped in fragment > dialog > fragment

## Summary

A button inside `fragment > dialog > fragment` (opened via the outer fragment's
`on_click`) does not increment or rerun on Streamlit 1.62+. This worked on
1.61.1 and 1.59.2. The click is dropped because the nested fragment IDs are
evicted from fragment storage after the opener fragment reruns.

## Finding

**Bug confirmed.** Playwright against released wheels:

| Version | Increment result | Verdict |
|---------|------------------|---------|
| 1.59.2 (reporter last-good) | Count 0 → 1 | works |
| 1.61.1 | Count 0 → 1 | works |
| 1.62.0 | Count stays 0 | **broken** |
| 1.64.0 (reported / latest) | Count stays 0 | **broken** |
| `origin/develop` (includes #17039) | Count 0 → 1 | **already fixed** |

On 1.62–1.64 the server logs:

```
The fragment with id <id> does not exist anymore - it might have been
removed during a preceding full-app rerun.
```

The dialog UI still shows Increment; only the BackMsg is ignored.

## Reproduction

App: `repro_gh_17112.py` (minimal form of the reporter snippet: outer
`@st.fragment` opener with `on_click=@st.dialog`, inner `@st.fragment`
Increment + `st.rerun(scope="fragment")`).

Playwright (`verify_gh_17112.py`): open dialog, click Increment, assert Count
is 1. Assertion fails on 1.62+ (bug present). Screenshots:
`after_increment_1.64.png` (Count still 0) vs `after_increment_1.59.2.png`
(Count is 1).

## Root Cause

Introduced by [#16314](https://github.com/streamlit/streamlit/pull/16314)
(`01b1c21ad1`, first in **1.62.0**): after a fragment-only rerun, ScriptRunner
calls `FragmentStorage.clear_stale_descendants` so nested fragments that the
ancestor did not re-register are dropped (needed for coalesced `run_every`
parents/children, #10719).

This repro hits a different path:

1. Click **Open Counter** → fragment rerun of the **outer** fragment.
2. `on_click` runs `@st.dialog`, which wraps its body in `_fragment(...)`
   (`dialog_decorator.py`). That dialog fragment (and the inner Increment
   fragment, whose parent is captured while the dialog fragment is current)
   is registered **during the callback**, before the outer fragment body runs.
3. The outer body only re-renders the Open Counter button; it does not call
   the dialog function again, so those IDs are not in
   `ids_registered_after(registration_sequence_before)`.
4. `clear_stale_descendants` evicts them. The dialog deltas are already on
   the frontend, so the modal stays open.
5. Click Increment → client sends `fragment_id` for the evicted fragment.
6. `AppSession` bails out if `not self._fragment_storage.contains(fragment_id)`
   (`app_session.py` ~469–475) and never applies widget state or runs the
   fragment. The action is dropped with no user-visible error.

`#16314` is correct for inline nested `run_every` fragments; it is too
aggressive when a descendant fragment is created only in a parent-fragment
**callback** (dialogs opened via `on_click`).

**Already fixed on develop** by [#17039](https://github.com/streamlit/streamlit/pull/17039)
(same bug as #17011: dialog fragments are `FULL_APP_SCOPED` so parent-fragment
reruns do not evict them). Re-verified this issue's repro on
`origin/develop` after that merge.

**Workaround until the next release:** open the dialog from the parent fragment
body (session-state flag), not `on_click`. The published `app.py` includes a
live workaround demo, verified on 1.64.0 by
`verify_workaround_gh_17112.py` (Count reaches 1 via the workaround dialog
while the `on_click` dialog in the same app still fails).

## Classification

- **Type:** Bug (regression)
- **Status:** Confirmed on 1.62.0–1.64.0; last good 1.61.1; already fixed on develop (#17039)
- **Areas:** backend, fragments / dialogs (`runtime/fragment.py`,
  `runtime/scriptrunner/script_runner.py`, `runtime/app_session.py`,
  `elements/dialog_decorator.py`)
- **Priority:** P2 — less-noticeable regression in a specific nesting
  (`fragment` opener + `on_click` dialog + nested fragment). Not a primary
  journey for most users (below the P1 “>5% will notice” bar), but it is a
  silent functional regression with a workaround, which
  `wiki/issue-prioritization.md` maps to at least P2.
- **Fix complexity:** Medium — eviction is load-bearing for #10719; the fix
  must keep coalesced ancestor/descendant `run_every` safe while not dropping
  callback-created dialog fragments.
