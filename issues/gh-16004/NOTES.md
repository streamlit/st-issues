# Issue #16004 — st.selectbox Escape no longer clears the typed search query since 1.59.0

**Status:** Bug confirmed — regression
**Priority:** P2 (low end; see rationale)
**Type:** Regression
**Areas:** `st.selectbox`, frontend, react-aria

---

## Summary

Since 1.59.0 (the BaseWeb → react-aria `ComboBox` migration, PR #15438), pressing
**Escape** while searching a value-selected `st.selectbox` no longer discards the
typed query. The dropdown closes and the committed value is correctly preserved, but
the half-typed query stays visible in the input, so the box shows text that does not
match the actual value. In 1.58.0, Escape cleared the query and restored the
committed label. Only the **Escape** path regressed — clicking away (blur) still
restores correctly on both versions.

## Evidence

Verified programmatically with Playwright against **released PyPI wheels** in
throwaway `uv` environments. App: `st.selectbox("Fruit", FRUITS, index=2)` with
`Banana` committed; type `gr`, then either press Escape or blur.

| Version | Component | After typing `gr` + **Escape** | After typing `gr` + **blur** (control) | Result |
|---------|-----------|-------------------------------|----------------------------------------|--------|
| 1.58.0  | BaseWeb `Select`       | input cleared → shows `Banana` | shows `Banana` | PASS (works) |
| 1.59.0  | react-aria `ComboBox`  | input keeps `Bananagr` (stale query) | shows `Banana` | **FAIL (bug)** |

- The committed `value` stays `Banana` on both versions — no wrong commit; the bug
  is purely the stale display text in the input.
- Screenshots: `escape_1.59.0.png` (stale `Bananagr` after Escape), `escape_1.58.0.png`
  (restored `Banana`), plus `blur_1.59.0.png` / `blur_1.58.0.png` for the control.

> **DOM note on the two components.** BaseWeb (1.58.0) keeps the committed value in a
> separate value `<div value="Banana">` and leaves the search `<input>` empty when not
> filtering; Escape clears the input and restores the div. react-aria (1.59.0) holds
> the committed value in the input's own `value`, and Escape leaves the typed query
> there. On the released 1.59.0 wheel plain typing shows `Bananagr` (the separate
> append bug #15985 is still present there); on current `develop` (with the #15996
> append fix) the input instead shows just `gr` after Escape — still not discarded.

## Version Bracket

| Version | Status  | Notes |
|---------|---------|-------|
| 1.58.0  | Working | BaseWeb `Select`; Escape clears the query |
| 1.59.0  | Broken  | react-aria `ComboBox` migration (PR #15438) |
| develop | Broken  | Confirmed by source inspection — no Escape-restore for non-clearable selectboxes |

## Root Cause

**File:** `frontend/lib/src/components/shared/Dropdown/Selectbox.tsx`

`handleInputKeyDownCapture` handles Escape **only** for *clearable* selectboxes:

```tsx
if (e.key === "Escape" && clearable && !isNullOrUndefined(valueRef.current)) {
  e.preventDefault()
  commitSelection(null)   // clear to None
}
```

For a **non-clearable** selectbox (the default), there is no Escape handler, so
Escape falls through to react-aria's `<ComboBox>`. RAC closes the dropdown but never
resets the **controlled** `inputValue` — Streamlit owns that state and doesn't touch
it on Escape, so the typed query survives.

The blur path already does the right thing (`handleBlur`):

```tsx
const handleBlur = useCallback((): void => {
  const target = valueRef.current ?? ""
  if (inputValueRef.current !== target) {
    setInputValue(target)   // restore committed label
  }
  setFilterActive(false)
}, [])
```

Escape has no equivalent, which is exactly why blur restores but Escape does not.

### Suggested Fix

Add an Escape branch for the non-clearable case that mirrors `handleBlur` — restore
the committed label, clear the active-filter state, and close the dropdown. Roughly:

```tsx
if (e.key === "Escape" && !clearable) {
  e.preventDefault()
  setInputValue(valueRef.current ?? "")
  setFilterActive(false)
  closeDropdownRef.current?.()
}
```

(The existing clearable branch is unaffected: clearable selectboxes still clear to
`None` on Escape via their own code path.)

## Classification

- **Type:** `type:bug`, regression
- **Introduced:** PR #15438 (BaseWeb → react-aria migration, 1.59.0)
- **Area:** `st.selectbox` / frontend / react-aria
- **Fix complexity:** Small — one Escape branch mirroring the existing blur-restore.
- **Workaround:** Click away (blur) instead of pressing Escape; the committed value
  is restored. The value itself is never corrupted, only the display text.

## Priority Recommendation: P2 (low end)

Per `wiki/issue-prioritization.md`, regressions bias upward and "a less noticeable
regression … or confusing behavior" is **at least P2**, which sets the floor here.
It is not P1:

- **Reach by broken behavior, not surface.** It only bites when a user (a) has a
  committed value, (b) types a partial query, and (c) dismisses with **Escape**
  specifically rather than clicking away — a narrow, power-user interaction. The
  common type-to-search-then-pick / click-away journeys are intact.
- **Harm is mild and self-correcting.** The committed `value` is never wrong (still
  `Banana`); only the input's display text is stale, and it restores on the next
  blur. No data loss, no incorrect selection.
- **Clear workaround** (blur instead of Escape).

This is the **mildest of the three 1.59.0 selectbox regressions**: milder than
sibling #16003 (P2, options silently disappear on the default filter) and far milder
than overlay bugs like #15859 (P1) where a widget is visibly unusable. A reasonable
case exists for **P3** if the team discounts the cosmetic, self-correcting nature and
the Escape-specific trigger; P2 is chosen to honor the "regression ≥ P2" floor and
to stay consistent with the sibling selectbox regressions.
