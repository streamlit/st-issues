# Issue #16003 — st.selectbox fuzzy search only matches contiguous substrings since 1.59.0

**Status:** Bug confirmed — regression  
**Priority:** P1  
**Type:** Regression  
**Areas:** `st.selectbox`, frontend, react-aria  

---

## Summary

Since 1.59.0, `st.selectbox` fuzzy search (`filter_mode="fuzzy"`, the default) only
matches options where the query is a **contiguous substring** of the label. In 1.58.0
the search was truly fuzzy (non-contiguous subsequence), so typing `ape` matched both
`Grape` and `Apple`. After the migration, `Apple` is silently dropped and queries like
`aple` / `rp` that require non-contiguous matching return "No results".

## Evidence

Verified programmatically with Playwright on **Streamlit 1.59.0** (PyPI wheel,
`uv venv` throwaway environment):

| Query | Expected (1.58.0) | Actual (1.59.0) | Result |
|-------|------------------|-----------------|--------|
| `ape`  | Grape, Apple      | Grape only      | FAIL   |
| `aple` | Apple             | No results      | FAIL   |
| `rp`   | Grape             | No results      | FAIL   |

Screenshots captured at time of verification — `ape` shows only `Grape` in the
dropdown; `aple` and `rp` show the "No results" state.

## Version Bracket

| Version | Status  | Notes |
|---------|---------|-------|
| 1.58.0  | Working | BaseWeb `Select` component |
| 1.59.0  | Broken  | react-aria `ComboBox` migration (PR #15438) |
| develop | Broken  | No fix applied yet in `main`/`develop` as of 2026-07-15 |

## Root Cause

**File:** `frontend/lib/src/components/shared/Dropdown/Selectbox.tsx`

The `<ComboBox>` component (lines 486–556 in current develop) has no `defaultFilter`
prop. React Aria's `ComboBox` applies its own built-in `contains` text filter to the
collection. Since Streamlit passes the already-fuzzy-filtered `displayOptions` as
`items` to `<StyledListBox>`, but RAC's internal collection still filters against
`inputValue` using `contains`, the visible list becomes the **intersection** of
Streamlit's fuzzy filter and RAC's substring filter — effectively substring-only.

Streamlit's own `fuzzyFilterSelectOptions` in
`frontend/lib/src/util/fuzzyFilterSelectOptions.ts` is correct in isolation — it
already returns the right fuzzy matches. The second filter from RAC strips away valid
non-contiguous matches.

### Suggested Fix

Pass a no-op `defaultFilter` to `<ComboBox>`:

```tsx
<ComboBox
  // ...existing props...
  defaultFilter={() => true}
>
```

This tells React Aria to skip its own filter because Streamlit's filter is already
applied to `displayOptions`. Per the
[React Aria docs](https://react-spectrum.adobe.com/react-aria/ComboBox.html#custom-filtering),
`defaultFilter` is the documented extension point for custom filtering.

## Fix in Progress

PR **#16009** (by @LuC-9) implements the `defaultFilter={() => true}` fix and includes
Vitest regression tests covering `ape → [Grape, Apple]` and `aple → [Apple]`. The PR
should be reviewed promptly given P1 priority.

## Classification

- **Type:** `type:bug`, regression  
- **Introduced:** PR #15438 (BaseWeb → react-aria migration, 1.59.0)  
- **Area:** `st.selectbox` / frontend / react-aria  
- **Workaround:** None clean. Users can set `filter_mode='contains'` (different behavior)
  or `filter_mode='prefix'`, but there is no way to restore true fuzzy behavior without
  the code fix.

## Priority Recommendation: P1

Per `wiki/issue-prioritization.md`, P1 applies when there is a "non-blocking but
noticeable regression (>5% of users will notice) in a primary user journey or Streamlit
behavior, including behavior change that breaks backwards compatibility."

This regression:
- Affects `st.selectbox`'s **default** `filter_mode` — the behavior every user who
  does not explicitly pass `filter_mode` will experience.
- Is a backwards-incompatible behavior change between 1.58.0 and 1.59.0; the fuzzy
  search results silently narrow or disappear, leading users to believe options
  don't exist.
- Has **no clean workaround** (changing `filter_mode` alters documented behavior).
- Has a known, low-risk, one-line fix already in PR #16009.

The closest wiki example at P1 is #15859 (`st.date_input` calendar regression in
1.59.0) — same release, same root PR (#15438), similar scope and fix complexity. This
issue merits the same treatment.
