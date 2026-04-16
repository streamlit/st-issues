# gh-14814: st.radio unable to select other option (custom class + format_func)

## Summary

`st.radio` cannot select options other than the first (or `index`-set default) when using custom class instances as options with a `format_func`. Selection always snaps back to the default.

## Root Cause

In `lib/streamlit/elements/widgets/radio.py` (line 551-552), `validate_and_sync_value_with_options()` is called **without** passing the user's `format_func`:

```python
current_value, value_needs_reset = validate_and_sync_value_with_options(
    cast("T | None", widget_state.value), opt, index, key
)
```

The function signature has `format_func: Callable[[Any], str] = str` — when omitted, it defaults to `str()`. For custom objects without `__str__`, `str()` produces memory-address-based representations that differ across reruns, causing validation to always conclude the selected value is invalid and reset to default.

All other single-select widgets correctly pass `format_func`:
- `st.selectbox` (line 714-715): `validate_and_sync_value_with_options(widget_state.value, opt, index, key, format_func)`
- `st.select_slider` (line 561-565): same pattern

## Fix

Pass `format_func` to the validation call in `radio.py`:

```python
current_value, value_needs_reset = validate_and_sync_value_with_options(
    cast("T | None", widget_state.value), opt, index, key, format_func
)
```

## Classification

- **Type:** Bug
- **Priority:** P2 (widget broken for specific but common use case)
- **Labels:** `feature:st.radio`, `area:widgets` (already present)
- **Affected version:** 1.56.0 (reported), likely present since `validate_and_sync_value_with_options` was introduced/refactored
