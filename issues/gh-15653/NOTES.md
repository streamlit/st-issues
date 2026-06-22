# gh-15653: date_input hover effect varies with min_value

## Summary

Reporter observed that hovering over `st.date_input` calendar dates shows a hover
effect (a highlight ring) for some `min_value` values but not others:

- `min_value` within the current month (e.g. 7 days ago) → "no hover effect"
- `min_value` in the previous month (e.g. 31 days ago) → hover effect appears

## Finding

**Working as intended.** The hover highlight applies only to **selectable**
(enabled) dates. Out-of-range dates are disabled and intentionally do not show a
hover effect. Changing `min_value` only changes *which* dates are selectable — the
hover behavior itself is consistent across both configurations.

The reporter's two screenshots differ solely because of which dates are enabled:

| Date hovered | Case A (`min_value` = Jun 15) | Case B (`min_value` = May 22) |
| ------------ | ----------------------------- | ----------------------------- |
| Jun 18 (in range both) | hover ring shows | hover ring shows |
| Jun 4 (early month) | **disabled** → no ring | **enabled** → ring shows |

The reporter was almost certainly hovering over disabled early-month dates in
Case A.

## Reproduction

Reproduced on Streamlit `1.58.0` via `make debug` + Playwright. Verified at the
DOM level by inspecting the Jun 4 cell in each calendar:

```
Case A (min=7d):  aria-label="Not available. Thursday, June 4th 2026."        cursor=default  color=grey
Case B (min=31d): aria-label="Choose Thursday, June 4th 2026. It's available." cursor=pointer  color=dark
```

Hovering an enabled date (Jun 18) showed the highlight ring in **both** cases,
confirming the hover effect is consistent for selectable dates.

## Classification

- **Type:** Not a bug — working as intended
- **Status:** Reproduced; behavior explained
- **Areas:** frontend, date_input / calendar widget (BaseWeb Datepicker)
- **Priority:** N/A
- **Suggested response:** Hover applies to selectable dates only; disabled
  (out-of-range) dates correctly show no hover. The difference observed is due to
  which dates `min_value` makes selectable.
