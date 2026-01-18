# Issue #12678 - Fix Implementation Summary

**Issue:** Plots are shown tiny, fixed after maximizing and unmaximizing plot again - v1.50.0
**Fix Date:** 2025-10-18
**Implemented By:** AI Agent
**Issue URL:** https://github.com/streamlit/streamlit/issues/12678
**Related Issue:** #12763 (duplicate)

---

## Summary

Successfully implemented fix for v1.50.0 regression where plots and images rendered at 16px width in fragments, expanders, and containers. The fix uses conditional width override based on widthConfig while preserving the horizontal alignment fix from #12435.

---

## Changes Implemented

### Primary Change

**File:** `frontend/lib/src/components/core/Block/StyledElementContainerLayoutWrapper.tsx` (lines 160-171)

**Before (v1.50.0 - broken):**
```tsx
} else if (node.element.type === "imgs") {
  styles.width = "auto"  // Always auto
}
```

**After (fixed):**
```tsx
} else if (node.element.type === "imgs") {
  // Use "auto" when image has explicit non-stretch size (content/pixel/rem) to enable horizontal alignment (#12435).
  // Use "100%" when using stretch or no width config to ensure container has dimensions for width calculation (#12678).
  const isUsingStretchOrDefault =
    !node.element.widthConfig || node.element.widthConfig.useStretch
  styles.width = isUsingStretchOrDefault ? "100%" : "auto"
}
```

### Test Files Created

**New E2E Tests:** `e2e_playwright/st_pyplot_image_width_regression_test.py`
- 6 tests covering fragments, expanders, containers, and workaround
- Tests verify actual rendered width (> 200px, not 16px)
- Provides regression protection for future releases

**Test App:** `e2e_playwright/st_pyplot_image_width_regression.py`
- 5 test scenarios
- Covers all affected contexts
- Includes workaround verification

---

## Root Cause

**Problematic Commit:** `4954237e7d` (Sept 11, 2025)
**Title:** "[fix] horizontal alignment of st.image in vertical containers"
**Issue Fixed:** #12435

**What Went Wrong:**

The commit changed imgs container from `width: "100%"` to `width: "auto"` to enable horizontal alignment. This created a width calculation problem:

1. Parent container: `width: "auto"` (depends on content)
2. Child frame: `width: "100%"` (100% of auto = 0px on initial render)
3. useCalculatedDimensions(): measures 0px or 16px
4. Images render tiny until layout recalculation

**Why Fix Works:**

- Default/stretch width → `"100%"` provides definite width for calculation
- Content/pixel width → `"auto"` enables alignment while explicit size prevents calculation issue
- Preserves both fixes (#12435 and #12678)

---

## Testing

### Automated Tests

**Regression Tests Created:**

All 6 tests PASS:
1. `test_pyplot_in_fragment_width` - Verifies plots are not 16px in fragments
2. `test_pyplot_in_fragment_with_workaround` - Verifies width="content" workaround
3. `test_pyplot_in_expander_width` - Verifies plots in expanders
4. `test_pyplot_in_expander_with_workaround` - Verifies workaround in expanders
5. `test_pyplot_in_container_width` - Verifies plots in containers
6. `test_all_pyplot_elements_present` - Verifies all elements render

**Before Fix:** Tests failed at 16px width
**After Fix:** Tests pass with width > 200px

### Manual Testing

**Test App:** `test_fix.py` in this directory

**Test Scenarios:**
1. Plot in fragment (primary bug)
2. Plot in expander (#12763)
3. Plot in container
4. Plot with width="content" (workaround)
5. Image with horizontal alignment (#12435 regression check)

**Run:** `streamlit run test_fix.py`

**Expected Results:**
- All plots display at full/normal width
- No 16px tiny plots
- Horizontal alignment still works
- All contexts render correctly

### Regression Verification

**Existing Tests Still Pass:**
- ✅ st_image_test.py
- ✅ st_pyplot_test.py
- ✅ st_layouts_container_alignment_test.py (preserves #12435)

---

## Backward Compatibility

✅ **Fully Backward Compatible**

- No API changes
- No behavior changes for users
- Simply fixes the regression
- Preserves horizontal alignment feature

**Width Parameter Behavior:**
- No `width` param → stretch (default) → width: 100% ✅ Fixed
- `width="stretch"` → width: 100% ✅ Fixed
- `width="content"` → width: auto ✅ Works (alignment preserved)
- `width=200` → width: auto ✅ Works (alignment preserved)

---

## Impact

### Issues Resolved

- **#12678** - Primary issue (plots tiny in fragments) ✅
- **#12763** - Duplicate (images tiny in expanders) ✅

### Users Affected

- Users using st.pyplot or st.image in `@st.fragment`
- Users using st.pyplot or st.image in `st.expander`
- Users using st.pyplot or st.image in `st.container`
- Regression affects v1.50.0 only

### Workaround No Longer Needed

Users can remove the `width="content"` workaround after this fix is deployed.

---

## Implementation Notes

### Key Insights

1. **Conditional Logic is Critical:**
   - Can't use "100%" for all cases (breaks alignment)
   - Can't use "auto" for all cases (breaks width calculation)
   - Must be conditional based on explicit width config

2. **Width Calculation Timing:**
   - useCalculatedDimensions() is async (ResizeObserver)
   - "auto" + "100%" child = 0px on first render
   - Explicit "100%" parent = proper calculation

3. **Fragment Behavior:**
   - Fragments wrap content in st.container() automatically
   - Container has width="stretch" by default
   - This triggers the width calculation path

### Testing Strategy

- Bounding box measurements (not just snapshots)
- Actual pixel width verification
- Multiple contexts (fragments, expanders, containers)
- Workaround validation
- Regression checks

---

## Files Modified

**Frontend:**
- `frontend/lib/src/components/core/Block/StyledElementContainerLayoutWrapper.tsx`

**Tests Added:**
- `e2e_playwright/st_pyplot_image_width_regression.py`
- `e2e_playwright/st_pyplot_image_width_regression_test.py`

**Documentation:**
- `.cursor/commands/bug_bash/notes/gh-12678-root-cause.md` (updated)
- This file (implementation summary)
- `test_fix.py` (manual test app)

---

## Timeline

- **Oct 2, 2025:** Issue #12678 reported
- **Oct 6, 2025:** Confirmed reproduction with fragments
- **Oct 11, 2025:** Issue #12763 reported (duplicate)
- **Oct 16-17, 2025:** Root cause analysis, Playwright tests created
- **Oct 18, 2025:** Fix implemented and verified

---

## Deployment

Once merged and deployed:

1. Update both issues (#12678, #12763) with fix information
2. Users can upgrade to get the fix
3. Workaround (`width="content"`) is no longer necessary
4. No action required from users (automatic fix)

---

## Notes for Reviewers

- Fix is minimal and surgical (only changes imgs width logic)
- Preserves both the original alignment fix and fixes the regression
- Comprehensive test coverage added
- All existing tests pass
- No breaking changes
- Ready for release
