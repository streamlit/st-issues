# Pending Actions for Issue #12782

## Status: Likely Duplicate / Intended Behavior

Unable to reproduce the reported issue. Team member (lukasmasuch) identified this as likely the same underlying issue as #12629, which is labeled as `status:intended-behavior` due to the `key_as_main_identity` changes in 1.50.0.

## What Was Tested

### Attempt 1: Clearing Widget Key

- Parent `on_change` clears the multiselect's widget key
- **Result:** Bug did not reproduce - defaults worked correctly

### Attempt 2: Options Change Without Clearing

- Parent changes cause options to change
- Widget key persists with OLD values
- Separate session state key holds defaults
- Multiselect has `on_change` callback
- **Result:** Bug did not reproduce - multiselect correctly falls back to defaults

### Attempt 3: Fix Reproduction Logic (Current)

- **Critical fix:** Changed to only initialize `selected_conversation` once (on first load)
- Previously was updating it every fragment run, which masked the bug
- Now `selected_conversation` keeps OLD values when patient changes
- This properly tests if `default` parameter works when it has invalid values
- **Result:** Testing in progress

### Attempt 4: Python Version Testing (Skipped)

- Initially added Pipfile for Python 3.12 (reporter used 3.12.9)
- Removed to allow testing on community cloud first
- Can add back later if bug only reproduces on Python 3.12

## Observed Behavior

When testing with Patient A → Patient B transition:

- ✅ Widget key correctly shows old value: `['Initial Consultation']`
- ✅ Warning correctly displayed: "Widget key contains values from OLD options"
- ✅ Default source key has correct value: `['Emergency Visit']`
- ✅ **Multiselect correctly displays the default value**
- ✅ No empty state observed

## Possible Explanations

1. **Bug Already Fixed:** The issue may have been fixed after 1.50.0 was released
2. **Missing Crucial Element:** There's some aspect of the reporter's complex setup we haven't captured:
   - More complex conditional logic
   - Nested fragments
   - Specific timing of state updates
   - Other widgets/state interactions
3. **Version-Specific:** Might require exact version 1.50.0 (not 1.50.x or later)
4. **Expected Behavior:** The behavior the reporter observed might actually be expected in some edge cases

## Reporter's Own Statement

From the issue:

> "Unfortunately, I couldn't reproduce the issue in a minimal code snippet — so it seems related to a more complex interaction between fragments, nested state logic, and conditional UI loading."

The reporter themselves couldn't create a minimal reproduction, which suggests this is a very specific/complex interaction.

## Next Steps

### Option 1: Request More Information

Comment on the issue asking for:

- Exact Streamlit version (1.50.0, 1.50.1, etc.)
- More complete code example that reproduces the issue
- Whether the issue still occurs in latest version
- Steps to reproduce in their actual app

### Option 2: Wait for Clarification

Since reporter says they have a workaround, wait to see if:

- Other users report the same issue
- Reporter can provide more details
- Issue reproduces in other contexts

### Option 3: Mark as Unable to Reproduce

Add comment explaining:

- Multiple reproduction attempts made
- Bug does not occur in test scenarios
- Request reporter provide reproduction that demonstrates the issue
- Keep issue open for further investigation

## Team Response (Oct 15, 2025)

**Lukas Masuch (@lukasmasuch) identified this as related to #12629:**

- Issue #12629: "Regression (1.50.0): widget value no longer updates when dependent on another widget"
- Status: `status:intended-behavior`
- Root cause: Changes to support `key_as_main_identity` in 1.50.0
- Related comment: https://github.com/streamlit/streamlit/issues/12629#issuecomment-3361642792

**Agent (@sfc-gh-lwilby) suggested workaround:**

- Try removing the `key` parameter from the multiselect
- This may resolve the issue if it's related to the `key_as_main_identity` behavior

## Next Steps

### Awaiting Reporter Response

Wait for reporter (@csipapicsa) to respond to:

1. Whether removing the `key` resolves the issue
2. Whether the workaround they found is acceptable
3. Whether they can confirm it's the same issue as #12629

### If Confirmed as Duplicate

If reporter confirms this is the same as #12629:

1. Close as duplicate of #12629
2. Add link to #12629 in closing comment
3. Note in journal: Related to `key_as_main_identity` changes (intended behavior)
4. Keep reproduction app for reference

### If Different Issue

If reporter provides more details showing it's a different issue:

1. Request more complete reproduction code
2. Re-evaluate with new information
3. Update reproduction app accordingly

## Reproduction App

Available at: https://issues.streamlit.app/?issue=gh-12782

Status: Unable to reproduce the reported behavior in test scenarios
