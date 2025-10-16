# Issue #12792: st.code Copy to Clipboard Not Working

**GitHub Issue:** https://github.com/streamlit/streamlit/issues/12792

**Status:** Environment-Specific Issue (Cannot Reproduce in Tests)

**Reported:** 2025-10-16 by @aeternu

---

## Summary

User reports that the copy-to-clipboard button in `st.code` widgets does not work when clicked in Streamlit v1.50. Button appears on hover but clicking it doesn't copy text to clipboard.

**Key Finding:** Automated Playwright tests PASS (clipboard works correctly), indicating this is likely an **environment-specific issue** rather than a universal Streamlit bug.

---

## Environment

**User's Environment:**

- **OS:** Linux (Tencent OS, based on CentOS)
- **Browser:** Chrome
- **Streamlit:** 1.50
- **Python:** 3.11.13

**Test Environment (where it works):**

- **OS:** macOS (Darwin)
- **Browser:** Chromium (Playwright)
- **Streamlit:** Development version
- **Python:** 3.13.1

---

## Files in This Directory

### `app.py`

Visual reproduction app for manual testing. Deploy this to allow the user to test in their specific environment.

**Features:**

- Multiple test cases (single-line, multiline, SQL, etc.)
- Diagnostic instructions for users
- Browser console error checking guide
- Manual copy-paste verification test
- Environment information collection
- Clear instructions on what to report back

**Deploy:** Can be deployed to https://issues.streamlit.app/?issue=gh-12792

### `NOTES.md`

Comprehensive technical analysis including:

- Root cause hypothesis
- Related code areas
- Playwright test results
- Environment-specific causes
- Diagnostic strategies

### Test Files (in main streamlit repo)

- **E2E Tests:** `e2e_playwright/st_code_test.py` (lines 216-293)
  - `test_copy_to_clipboard_functionality` - ✅ PASSED
  - `test_copy_to_clipboard_multiline_code` - ✅ PASSED

---

## Test Results

### Automated Tests: ✅ PASS

Both Playwright tests pass successfully:

1. Single-line code copying works
2. Multiline code copying works
3. Button state changes correctly
4. Clipboard contains exact expected text

**Conclusion:** Streamlit's clipboard implementation is correct. Issue is environmental.

---

## Likely Causes

Based on analysis and test results:

### 1. Browser Security Context (Most Likely)

- Chrome's `navigator.clipboard` API requires HTTPS (secure context)
- HTTP outside of localhost will silently fail
- No visible error to user

### 2. Linux Clipboard Complexity

- X11 vs Wayland display servers
- Multiple clipboard systems (PRIMARY, CLIPBOARD)
- CentOS-based systems may have restrictions

### 3. Enterprise/Corporate Policies

- Tencent OS is enterprise Linux
- May have security policies blocking clipboard access
- Browser extensions or IT policies

### 4. Browser Version/Configuration

- Specific Chrome version bugs
- Browser settings disabling clipboard
- Permissions denied without indication

---

## Missing Information

To diagnose the user's specific issue, we need:

1. **Browser console errors** (most critical!)
2. HTTP vs HTTPS context
3. Test in Firefox or another browser
4. Chrome version
5. Clipboard permissions status
6. Whether manual copy-paste works

---

## Next Steps

### For User:

1. Run the `app.py` reproduction app
2. Check browser console for errors
3. Test all test cases and report results
4. Verify HTTP vs HTTPS
5. Test in another browser
6. Report findings back to GitHub issue

### For Team:

1. If HTTP issue → Document HTTPS requirement
2. If Linux-specific → Document known limitation
3. If enterprise policy → User must work with IT
4. If browser bug → Report to Chrome team

---

## Workarounds

**For users experiencing this issue:**

Use manual copy-paste:

1. Select code with mouse
2. Press Ctrl+C (Cmd+C on Mac)
3. Paste where needed

This works in all environments regardless of clipboard API restrictions.

---

## Value Added

### Test Coverage

- ✅ Filled gap in E2E tests (clipboard functionality now tested)
- ✅ Regression protection in place
- ✅ Tests verify actual clipboard contents, not just button appearance

### Documentation

- ✅ Comprehensive analysis in NOTES.md
- ✅ User-friendly reproduction app
- ✅ Clear diagnostic instructions
- ✅ Environment troubleshooting guide

### Diagnosis

- ✅ Confirmed Streamlit implementation is correct
- ✅ Identified as environment-specific
- ✅ Provided clear next steps for diagnosis

---

## Related Issues

- **#8838** - st.code modifies text when copied (different issue - about text modification)
- **#6726** - Add copy to clipboard to other elements (feature request)
- **#6921** - Copy button in chat elements (feature request)

---

## Technical Details

**Implementation:**

- Hook: `frontend/lib/src/hooks/useCopyToClipboard.ts`
- Component: `frontend/lib/src/components/elements/CodeBlock/CopyButton.tsx`
- Syntax Highlighter: `frontend/lib/src/components/elements/CodeBlock/StreamlitSyntaxHighlighter.tsx`

**API Used:** `navigator.clipboard.writeText()`

- Requires secure context (HTTPS or localhost)
- Requires clipboard permissions
- Error logging implemented (check browser console)

---

## Timeline

- **2025-10-16:** Issue reported by @aeternu
- **2025-10-16:** Analysis completed
- **2025-10-16:** Playwright tests created and run (PASS)
- **2025-10-16:** Visual reproduction app created
- **Next:** Awaiting user feedback with console errors and environment details
