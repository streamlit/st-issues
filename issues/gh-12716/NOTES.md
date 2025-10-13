# Issue #12716 Notes: Long Dialog Starts at Bottom

## Issue Summary

When a dialog has enough content to require a scrollbar, it starts scrolled to the bottom instead of the top. Users must scroll up to see the first entries.

## Reproduction Confirmed

**Status:** ✅ Bug reproduced by Streamlit team member

The issue is real and reproducible, but with an important caveat about when it occurs.

## Important Reproduction Details

### When the Bug DOES Occur

- Opening the dialog during normal app interaction
- Dialog has been opened, closed, and reopened
- After the initial app load and interaction

### When the Bug DOES NOT Occur

- ❌ First app run/load
- ❌ Immediately after clicking "Rerun" in Streamlit
- ❌ Fresh page load

**Implication:** The bug appears to be state-related. The dialog scroll position may be affected by previous dialog state or browser/DOM state that persists between dialog opens but resets on app rerun.

## Reproduction Protocol

**To reliably reproduce:**

1. Load the app at https://issues.streamlitapp.com/gh-12716
2. Click "Open Long Dialog"
3. **First time:** Dialog may open at top (correct)
4. Close the dialog using the "Close" button or X
5. Click "Open Long Dialog" again
6. **Second time:** Dialog opens at bottom (bug!)
7. You see "THIS IS THE BOTTOM" message and "Section 20" first
8. Must scroll UP to see "Section 1"

**To reset:**

- Click "Rerun" in Streamlit menu
- Refresh the browser page
- The bug will need to be triggered again by opening/closing/reopening

## Technical Analysis

### Code Review Findings

Searched the codebase (`frontend/lib/src/components/elements/Dialog/Dialog.tsx`) and found:

- **No explicit scroll handling:** No code to save or restore scroll position
- **Component unmounts:** When closed, Dialog returns `<></>` which should fully unmount
- **No intentional preservation:** No tests or comments about scroll position as a feature
- **No localStorage usage:** Dialog component doesn't use localStorage at all
  - (We do use localStorage for sidebar nav sections and theme, but not dialogs)
- **baseui Modal wrapper:** Uses baseui's Modal component which may have its own scroll behavior

### Root Cause Hypothesis

The behavior appears to be **unintentional** and likely caused by:

1. **Browser scroll position preservation:** Browser/DOM may be remembering scroll position between modal instances
2. **baseui Modal behavior:** The underlying baseui Modal component may not reset scroll on reopen
3. **React reconciliation:** React may be reusing DOM nodes that retain scroll state

The fact that it resets on rerun confirms this is **client-side state** (browser/React) not Streamlit state.

### Classification

✅ **This is a BUG, not deliberate behavior**

Evidence:

- No code intentionally preserves scroll position
- Behavior is inconsistent (works first time, breaks after)
- No documentation or tests for this behavior
- Unexpected UX (users must scroll up)

## Impact

**Severity:** Medium-High for UX

**Affected scenarios:**

- Forms in dialogs (users miss first fields)
- Instructions at top of dialogs
- Multi-step wizards in dialogs
- Any dialog opened multiple times in a session

**User workaround:** None - users must remember to scroll up after opening dialogs

## Testing Recommendation

For developers fixing this:

1. Test dialog open/close/reopen cycle
2. Verify scroll position resets on each open
3. Test with various dialog content lengths
4. Test across browsers (Chrome, Firefox, Safari, Edge)
5. Test on mobile devices

## Related Code

The reproduction app is at `/issues/gh-12716/app.py` and uses:

- `@st.dialog` decorator
- Multiple sections with `st.divider()` to create scrollable content
- Visual markers at top (red error box) and bottom (green success box)

---

**Created:** 2025-01-13
**Status:** Confirmed - reproducible with noted caveats
**App URL:** https://issues.streamlitapp.com/gh-12716
