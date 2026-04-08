# gh-14672: Conditional Block Type Change whitescreen (expander ↔ tabs)

## Summary

User reports a blank white screen when conditionally switching between `st.expander` and `st.tabs` via a checkbox. Claims this is a regression of the fix in PR #9276.

## Analysis

### Root cause investigation

PR #9276 ("Do not preserve children of a block if the block type changes") is present in the codebase. The fix in `AppRoot.addBlock` correctly checks `existingNode.deltaBlock.type === block.type` before inheriting children. This is covered by the unit test "removes a block's children if the block type changes for the same delta path".

### Reproduction attempt

- **Result:** Cannot reproduce on develop branch (v1.55.0-dev), which has the same relevant code as v1.56.0 (no changes to `AppRoot.ts`, `Block.tsx`, or `Tabs/` between these versions).
- **Browser:** Tested with Chromium via Playwright
- **Behavior:** Toggle between expander and tabs works correctly in both directions, no whitescreen, no console errors.

### Key observations

1. User is on **Firefox 149.0** — this could be a Firefox-specific rendering issue
2. User reports "no errors printed to console" — different from original #9259 which had `TypeError: e.node.deltaBlock is undefined`
3. The `time.sleep(1)` in the repro might create timing conditions not easily replicated
4. The tab_container block does NOT set `allow_empty = True`, while individual tabs do — in theory, if the tab container arrives before its children during a slow script run, it could render empty (`node.isEmpty && !node.deltaBlock.allowEmpty`)
5. Already asked user for clarification: full page crash vs. flicker (comment from sfc-gh-lwilby)

## Classification

- **Type:** Bug (cannot reproduce — may be browser-specific or intermittent)
- **Status:** Awaiting user response (already asked for clarification)
- **Areas:** frontend, element rendering, block reconciliation
- **Related:** PR #9276, Issues #9259, #8676

## Visual Reproduction App

**File:** `app.py`

**Created:** 2026-04-08

**Purpose:** Visual demonstration of issue #14672 for manual verification, particularly on Firefox

**App Features:**

- ✅ Demonstrates the exact reporter repro (expander ↔ tabs with checkbox + time.sleep)
- ✅ Includes additional test cases (reverse direction, tabs ↔ container)
- ✅ Highlights Firefox as the reported browser
- ✅ Links to original issue
- ✅ Self-contained and immediately runnable

**Testing Notes:**
- Must test on **Firefox** — could not reproduce on Chromium or WebKit
- Look for: whitescreen, brief flicker, or blank area when toggling checkbox
- Try toggling multiple times rapidly

**Deploy URL:** https://issues.streamlit.app/?issue=gh-14672
(Available after deployment)

## Repro app

```python
import streamlit as st

if st.checkbox("Click me!", True):
    with st.expander("Something", expanded=True):
        st.write("Do something 1")
        st.write("Do something 2")
        st.write("Do something 3")
        st.write("Do something 4")
        st.write("Do something 5")
        st.write("Do something 6")
else:
    tab1, tab2, tab3 = st.tabs(["1", "2", "3"])
    with tab1:
        st.info("Some info in tab1.")
    with tab2:
        st.info("Some info in tab2.")
    with tab3:
        st.info("Some info in tab3.")

import time
time.sleep(1)
```
