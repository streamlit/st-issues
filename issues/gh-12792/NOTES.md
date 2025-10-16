# Issue #12792 Analysis

**Issue URL:** https://github.com/streamlit/streamlit/issues/12792
**Analysis Date:** 2025-10-16
**Analyst:** AI Agent

## Issue Summary

**Title:** "Copy to Clipboard" button not work in st.code widget

**Type:** Regression

**Component:** st.code widget

**Severity:** Medium

**Reported Version:** Streamlit 1.50

## Problem Description

The "Copy to Clipboard" button in the st.code widget's upper right corner is not functioning. When users hover over the code block, the copy button appears, but clicking it does not copy the text to the clipboard. The user reports this as a regression - it used to work in previous versions of Streamlit.

## Reproduction Details

### Code Examples

```python
import streamlit as st

formatted_sql = "select * from expdatabase.exptable limit 200;"
st.code(formatted_sql, language="sql")
```

### Steps to Reproduce

1. Run the app in Streamlit 1.50 and Python 3.11.13
2. Hover over the st.code block (copy button appears)
3. Click the "Copy to Clipboard" button
4. Check clipboard contents

### Expected Behavior

The SQL text should be copied to the clipboard when the copy button is clicked. The button should show visual feedback (checkmark icon) indicating successful copy.

### Actual Behavior

Nothing happens when the copy button is clicked. The clipboard remains unchanged and no visual feedback is provided.

## Environment

- **Streamlit:** 1.50
- **Python:** 3.11.13
- **OS:** Linux (Tencent OS, based on CentOS)
- **Browser:** Chrome

## Error Messages

No error messages provided by the user. The functionality silently fails.

## Analysis

### Root Cause Hypothesis

Based on the codebase review, the clipboard functionality uses the `navigator.clipboard.writeText()` API (see `frontend/lib/src/hooks/useCopyToClipboard.ts`). The most likely causes for this failure are:

1. **Browser Security Context**: The Clipboard API requires a secure context (HTTPS) in most modern browsers. If the app is running on HTTP (localhost excluded), the API may be blocked.

2. **Browser Permissions**: Chrome on Linux may have stricter clipboard permission requirements. The user's browser might be blocking clipboard access due to security policies.

3. **Regression in v1.50**: Something may have changed in v1.50 that affects clipboard permissions or the event handling for the copy button.

4. **Linux-Specific Issue**: There might be Linux-specific clipboard handling issues, particularly with certain desktop environments (X11 vs Wayland) or enterprise Linux distributions like CentOS-based systems.

### Related Code Areas

Key files involved in clipboard functionality:

1. **`frontend/lib/src/hooks/useCopyToClipboard.ts`** (lines 76-89): The core clipboard hook that calls `navigator.clipboard.writeText()` and logs errors
2. **`frontend/lib/src/components/elements/CodeBlock/CopyButton.tsx`** (lines 31-60): The UI component that renders the copy button
3. **`frontend/lib/src/components/elements/CodeBlock/StreamlitSyntaxHighlighter.tsx`** (lines 101-105): Shows the copy button when code content is non-empty

The implementation includes error logging (`LOG.error("Failed to copy text to clipboard:", error)`), so if there's a JavaScript error, it should appear in the browser console.

### Related Issues

- **#8838** - "st.code modifies text when copied" - Different issue; that one is about text modification, not complete failure. Status: confirmed, P3
- **#6726** - Feature request to add copy to clipboard to other elements (not a bug report)

Not a duplicate. This appears to be a unique regression report.

### Browser Console Investigation Needed

The user should check their browser console for errors. The `useCopyToClipboard` hook logs errors, so any failure should be visible in the developer console.

## Reproducibility Assessment

**Can Reproduce:** Likely - but may be environment-dependent

**Confidence:** Medium

**Reasoning:**

- **Pros:**

  - Simple, clear reproduction code provided
  - User has provided complete environment details
  - Marked as regression (previously worked)
  - User followed all issue template guidelines

- **Cons:**
  - Clipboard functionality is notoriously browser/OS/security context dependent
  - May only reproduce in specific environments (Linux + Chrome + HTTP context)
  - Existing E2E tests verify button appearance but not actual clipboard functionality
  - No browser console errors provided

## Expected vs Bug Assessment

**Assessment:** Likely Bug (needs environment-specific reproduction)

**Confidence:** High

**Reasoning:**

1. **User reports regression**: Explicitly states it worked in previous versions
2. **Core functionality broken**: Copy to clipboard is a primary feature of st.code
3. **Clear user expectation**: Button is visible and interactive, should work when clicked
4. **Not documented limitation**: No documentation suggests clipboard should fail on Linux

However, there's a possibility this could be:

- An environmental/browser security issue outside Streamlit's control
- A permissions issue specific to the user's setup

**Team Consultation Needed:** No for initial reproduction, but may need input if reproduction shows it's a browser security limitation.

## Missing Information

While the issue is well-documented, additional helpful information:

1. **Browser console errors**: Check developer console for JavaScript errors when clicking copy button
2. **HTTP vs HTTPS**: Is the app running on HTTP or HTTPS? (localhost is usually exempt from HTTPS requirement)
3. **Which version worked**: User says it's a regression but didn't specify which version last worked
4. **Manual copy-paste works**: Can the user manually select and copy the text from the code block?
5. **Other browser test**: Does it work in Firefox or another browser on the same system?

These details would help narrow down if it's a Streamlit bug or environment-specific browser security issue.

## Playwright Test Feasibility

**Good Candidate for Playwright:** Yes - with caveats

**Reasoning:**

- Playwright has clipboard testing capabilities via `page.evaluate()` and browser context permissions
- Can grant clipboard permissions programmatically in tests
- Current tests only verify button appearance, not actual clipboard functionality
- Would add valuable regression protection

**Test Approach:**

1. Grant clipboard permissions to the test browser context
2. Click the copy button on an st.code element
3. Read clipboard contents via Playwright's clipboard API
4. Verify clipboard contains the expected code text
5. Verify button shows checkmark icon (copied state)

**Existing Test Gap:**

Current test `test_syntax_highlighting` only verifies the button appears on hover. No tests verify:

- Button actually copies to clipboard
- Checkmark icon appears after successful copy
- Clipboard contains correct text

**Example Playwright test pattern:**

```python
def test_copy_to_clipboard_functionality(app: Page):
    """Test that clicking copy button actually copies code to clipboard."""
    # Grant clipboard permissions
    context = app.context
    context.grant_permissions(["clipboard-read", "clipboard-write"])

    first_code_element = app.get_by_test_id("stCode").first
    copy_button = first_code_element.get_by_test_id("stCodeCopyButton")

    # Click copy button
    copy_button.click()

    # Read clipboard
    clipboard_text = app.evaluate("() => navigator.clipboard.readText()")

    # Verify
    expect(clipboard_text).to_equal("# This code is awesome!")
```

## Workarounds

**User Workarounds:**

1. **Manual copy-paste**: Users can still manually select and copy text from the code block
2. **Different browser**: Try Firefox or another browser
3. **HTTPS**: If running on HTTP, try HTTPS (though localhost should work)
4. **Downgrade**: Temporarily use Streamlit 1.49 if this is blocking

**No direct code workaround** available - this is a UI feature, not something that can be programmatically worked around.

## Playwright Test Results

**Test Execution Date:** 2025-10-16

**Environment:**

- Streamlit: Development version (from main branch)
- Python: 3.13.1
- Playwright: 0.7.1
- Browser: Chromium (headless)
- OS: macOS (Darwin)

### Test 1: `test_copy_to_clipboard_functionality`

**Test File:** `e2e_playwright/st_code_test.py` (lines 216-255)

**Result:** ✅ **PASSED**

**What the test verifies:**

1. Copy button appears on hover
2. Clicking copy button copies single-line code to clipboard
3. Clipboard contains exact expected text: `"# This code is awesome!"`
4. Button shows "Copied" state after successful copy

**Test Output:**

```
st_code_test.py::test_copy_to_clipboard_functionality[chromium] PASSED [100%]
```

### Test 2: `test_copy_to_clipboard_multiline_code`

**Test File:** `e2e_playwright/st_code_test.py` (lines 258-293)

**Result:** ✅ **PASSED**

**What the test verifies:**

1. Copy button works with multiline code blocks
2. Preserves newlines and indentation correctly
3. Clipboard contains complete function definition with proper formatting

**Test Output:**

```
st_code_test.py::test_copy_to_clipboard_multiline_code[chromium] PASSED [100%]
```

## Conclusion

**Issue Status:** Cannot Reproduce in Test Environment (Environment-Specific)

**Reasoning:**

1. **Both clipboard tests pass successfully** in our automated test environment
2. The clipboard functionality works correctly with both single-line and multiline code
3. Button state changes (visual feedback) work as expected
4. Text is copied accurately to clipboard including formatting

**This strongly suggests the issue is ENVIRONMENT-SPECIFIC, not a universal Streamlit v1.50 bug.**

### Why the User Might Be Experiencing the Issue

Given that our tests pass, the most likely causes are:

1. **Browser Security Context:**

   - User may be running on HTTP (not HTTPS) outside of localhost
   - Chrome's clipboard API requires secure context
   - Corporate/enterprise browser policies may block clipboard access

2. **Linux-Specific Clipboard Issues:**

   - X11 vs Wayland display server differences
   - Linux clipboard management is more complex (multiple clipboards: PRIMARY, CLIPBOARD)
   - CentOS-based systems may have additional security restrictions

3. **Enterprise Security Policies:**

   - Tencent OS is an enterprise Linux distribution
   - May have security policies blocking JavaScript clipboard access
   - Browser extensions or corporate policies may interfere

4. **Browser Version/Configuration:**
   - Specific Chrome version on Linux may have clipboard bugs
   - Browser flags or settings may disable clipboard access
   - Permission denied but no visible error to user

### Next Steps to Diagnose User's Issue

Since we cannot reproduce the bug, we need more information from the user:

1. **Browser Console Errors** - Critical to see if JavaScript errors are occurring
2. **Test on HTTPS** - Verify if HTTP vs HTTPS makes a difference
3. **Test on Different Browser** - Try Firefox to see if Chrome-specific
4. **Check Browser Permissions** - Verify clipboard permissions are granted
5. **Test Manual Copy** - Verify if manual select+copy works from code block
6. **Test on localhost** - Verify if works on localhost vs deployed app

## Visual Reproduction App

**App Created:** 2025-10-16

**File:** `app.py` in this directory

**Features:**

- 4 test cases covering different code types (single-line, multiline, SQL, longer code)
- Diagnostic instructions for users to check browser console
- Manual copy-paste verification test
- Environment information collection
- Clear step-by-step testing instructions
- Guidance on what to report back

**Purpose:**
Since automated tests pass, this app allows the user to test in their specific environment (Linux + Chrome + Tencent OS) and help diagnose the root cause.

**Deploy:** Can be deployed to https://issues.streamlit.app/?issue=gh-12792

## Next Steps

- [x] Create comprehensive analysis (this file)
- [x] Add Playwright tests for clipboard functionality (PASSED - cannot reproduce)
- [x] Create visual reproduction app for user testing
- [ ] Request more information from user (browser console, environment details)

## Notes for Future AI Agents

**Key Insights:**

1. **Clipboard API is security-sensitive**: Modern browsers restrict clipboard access to secure contexts (HTTPS) and may require user permissions. Linux environments can be particularly strict.

2. **Existing test coverage gap**: Current E2E tests verify visual appearance of the copy button but don't test actual clipboard functionality. This is why this regression might not have been caught.

3. **Error logging exists**: The `useCopyToClipboard` hook logs errors to console, so browser console output will be crucial for diagnosing this issue.

4. **Environment matters**: This may only reproduce in specific OS/browser/security contexts. The user is on Linux with Chrome, which has specific clipboard handling.

5. **Playwright clipboard testing**: Playwright supports clipboard testing with proper permissions setup. Adding this test would prevent future regressions.

**Investigation Strategy:**

1. First: Create simple reproduction app and test locally
2. If reproduces locally: Add Playwright test to confirm
3. If doesn't reproduce: Request browser console errors from user
4. Check if issue is specific to Linux/Chrome or affects other environments
5. Review any v1.50 changes to clipboard handling or event propagation

**Similar Issues to Monitor:**

- #8838 (st.code text modification) is related but different
- Any future clipboard-related issues should reference this analysis
