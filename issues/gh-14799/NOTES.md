# gh-14799: `st.date_input` min_value not respected

**Reporter:** thevolatilebit
**Created:** 2026-04-15
**Streamlit Version:** 1.56.0
**Labels:** type:bug, feature:st.date_input, upstream

## Summary

The year picker grid in `st.date_input` incorrectly greys out (disables) years that are within the valid `min_value`/`max_value` range. The years are still reachable via month arrow navigation — the issue is purely in the year-grid display.

## Root Cause

Upstream BaseWeb `Datepicker` component (v12.2.0). When rendering the year selection grid, BaseWeb checks whether the *currently viewed month/day* would be valid in each year, rather than checking whether *any* date in that year falls within the allowed range.

Example: `min_value=date(2026, 7, 7)`, `max_value=date(2029, 2, 1)` — year 2029 is greyed out because July 7 doesn't exist within the valid 2029 range (which only goes up to February 1).

## Duplicate of #9667

This is the same bug as #9667, which was confirmed and reproduced by @lukasmasuch. The maintainer noted it's an upstream improvement needed in the BaseWeb UI component.

## Classification

- **Type:** Bug (upstream)
- **Priority:** P3 — cosmetic/confusing but workaround exists (month arrows)
- **Disposition:** Close as duplicate of #9667
