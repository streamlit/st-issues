# Issue #13526: Markdown Ordered List Rendering Bug

## Issue Summary

**Title:** Markdown ordered list doesn't work if it starts with a number other than 1 and is preceded by a single newline character

**URL:** https://github.com/streamlit/streamlit/issues/13526

**Type:** Bug (Upstream issue)

**Status:** Needs triage

**Reported Version:** 1.52.2

## Problem Description

Markdown ordered lists fail to render correctly when:
- The list starts with a number other than 1 (e.g., 0, 10, etc.)
- The list is preceded by exactly 1 newline character

The same lists work correctly when:
- Starting with the number 1 (regardless of newlines)
- Preceded by 0 newlines (at start of string)
- Preceded by 2+ newlines

## Visual Reproduction App

**File:** `app.py`

**Created:** 2026-01-07

**Purpose:** Visual demonstration of markdown ordered list rendering issue for manual verification

**App Features:**
- ✅ Demonstrates all 9 test cases from the original issue
- ✅ Visual indicators showing which examples work vs broken (8 and 9 are buggy)
- ✅ Side-by-side comparison of markdown code and rendered output
- ✅ Detailed breakdowns of the bug examples
- ✅ Shows two workarounds (extra newline or start with 1)
- ✅ Links to original issue
- ✅ Self-contained and immediately runnable

**Testing Notes:**
- Focus on examples 8 and 9 - these should show lists not rendering as ordered lists
- Compare with examples 5 and 6 which work correctly (same starting numbers but 2 newlines)
- The bug is obvious: text shows "Something before: 0. foo 1. bar" instead of a proper ordered list

**Deploy URL:** https://issues.streamlit.app/?issue=gh-13526
(Available after deployment)

## Workarounds

### Workaround 1: Add extra newline
```python
# Instead of:
markdown = "Text:\n10. Item\n11. Item"

# Use:
markdown = "Text:\n\n10. Item\n11. Item"
```

### Workaround 2: Always start with 1
```python
# This always works regardless of newlines:
markdown = "Text:\n1. Item\n2. Item"
```

## Technical Details

- **Component:** st.markdown() rendering
- **Root Cause:** Upstream markdown library issue
- **Severity:** Medium - workaround exists but not obvious
- **Regression:** Yes - worked in earlier version

## Labels

- `type:bug` - Something isn't working as expected
- `feature:markdown` - Related to Markdown rendering
- `upstream` - Issue caused by upstream dependency
- `status:needs-triage` - Issue has not been triaged by the Streamlit team
