# gh-14671: Inconsistent space encoding in query params

## Summary

When using `bind="query-params"` on widgets, spaces are encoded as `%20`. But when `st.query_params["key"] = "value"` is used from the backend, spaces are encoded as `+`. When both are used together, the backend overwrites previously `%20`-encoded values with `+`.

## Analysis

### Root cause

Two different code paths handle query param URL encoding:

1. **Frontend** (`WidgetStateManager.ts:1383`): Uses `queryString.stringify()` from the `query-string` npm library → internally calls `encodeURIComponent` → encodes spaces as `%20`
2. **Backend** (`query_params.py:381`): Uses `urllib.parse.urlencode()` → internally calls `quote_plus` → encodes spaces as `+`

Both encodings are valid per RFC 3986 / HTML form spec, but the inconsistency causes confusing URL changes when both code paths interact.

### Fix approach

Align both paths to use `+` encoding (the longstanding `st.query_params` convention). The frontend's `queryString.stringify` in `WidgetStateManager.ts` could use a custom `encode` option to produce `+`-encoded spaces, or post-process the output to replace `%20` with `+`.

## Classification

- **Type:** Bug confirmed
- **Priority:** P3 (functional inconsistency, both encodings technically work)
- **Areas:** frontend, query-params
- **Feature:** `bind="query-params"` + `st.query_params` interaction
