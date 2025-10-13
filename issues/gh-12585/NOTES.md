# Issue #12585 Analysis: Selectbox Object Identity

## Issue Summary
`st.selectbox` returns copies of objects instead of the actual objects from the options list, breaking identity checks (using `is` operator). This is particularly problematic for singletons and patterns that rely on object identity.

## Related Issue History

### Issue #3703 (2021) - Original Report

**Timeline:**
- **Streamlit 0.83:** Worked correctly - returned actual objects
- **Streamlit 0.84:** **REGRESSION** - Started copying objects
- **Streamlit 0.86:** Started raising `ValueError` because copied objects didn't match options list
- **August 2021:** @vdonato acknowledged the issue, explained deepcopy is used for session_state callback mechanisms
- **July 2023:** @jrieke converted to `type:enhancement`, stating "the copying behavior is expected at this point"

**Current Status of #3703:** Open as enhancement, no resolution for 4+ years

## New Issue #12585 (2024) - What's Different?

### What's the Same:
- Same core problem: selectbox returns copies instead of actual objects
- Same impact: breaks identity checks (`is` operator)  
- Same use case concern: objects where identity matters

### New Information Provided:

1. **Confirms Persistence (4+ years later):**
   - Still broken in Streamlit 1.49.1
   - No progress since being marked "enhancement" in 2023

2. **Documentation Discrepancy:**
   - Docs state: "Returns: The selected option or None if no option is selected."
   - Reality: Returns a **copy** of the selected option
   - This is misleading to users

3. **Explicit Use Case:**
   - Mentions singleton patterns specifically
   - Concrete real-world impact

4. **Proper Verification (Critical Finding):**
   - Reproduction app includes test with `st.session_state` persisted objects
   - **Identity checks fail even with properly persisted objects**
   - This eliminates "user misunderstanding Streamlit execution model" explanation
   - Confirms this is genuine behavior, not user error

## Technical Analysis

### Why Deepcopy Was Introduced
According to @vdonato (2021), deepcopying was added to prevent mutations to return values from confusing session_state's callback mechanisms.

### The Problem with Deepcopy

**For Simple Types:** No issue - copies behave identically

**For Objects:** Major issues:
1. **Identity checks fail:** `selected is original_object` returns `False`
2. **Singleton pattern breaks:** Each "selection" is a new instance
3. **Object tracking impossible:** Can't track which specific instance user selected
4. **Caching/memoization breaks:** Object-based caches won't recognize copies

### Current Test Results

The reproduction app demonstrates:

**Test 1: Objects created in script body (original issue report)**
- Identity checks fail
- Could be explained by Streamlit's rerun behavior

**Test 2: Objects persisted in session_state (proper test)**
- Identity checks **STILL fail**
- Proves selectbox genuinely returns copies
- Not a misunderstanding of Streamlit execution model

## Assessment: Bug vs Expected Behavior?

### Arguments This Is A Bug:

1. **Documentation Mismatch:** 
   - Docs promise "the selected option" but deliver a copy
   - Users reasonably expect object identity to be preserved

2. **Was A Regression:**
   - Worked correctly in 0.83
   - Broke in 0.84
   - Breaking existing functionality typically qualifies as a bug

3. **Breaks Valid Use Cases:**
   - Singleton patterns
   - Object identity-based logic
   - Caching and memoization
   - Reference tracking

4. **No Progress As Enhancement:**
   - Marked enhancement 2+ years ago
   - No movement toward resolution
   - Users keep reporting it (like this new issue)

5. **Alternative Solutions Exist:**
   - Could use shallow copy instead of deepcopy for certain types
   - Could add option to disable copying for specific widgets
   - Could fix documentation if behavior won't change

### Arguments This Is Expected Behavior:

1. **Team Decision:**
   - Explicitly marked as "expected behavior" by @jrieke in 2023
   - Intentional design choice

2. **Technical Necessity:**
   - Deepcopy protects session_state callback mechanisms
   - May be required for internal consistency

3. **Labeled As Enhancement:**
   - Suggests fixing it is a "nice to have" not a critical bug
   - Implies current behavior is acceptable

## Possible Solutions

### Option 1: Accept As Expected, Fix Documentation
- Update docs to clearly state selectbox returns copies
- Add guidance on working with object identity
- Minimal code changes

### Option 2: Make Copying Optional
- Add parameter like `copy_selection=True` (default for backward compatibility)
- Allow users to opt out when they need identity preservation
- Requires API change

### Option 3: Smart Copying
- Only deepcopy when necessary (e.g., when callbacks are involved)
- Use shallow copy or no copy when safe
- Requires careful implementation

### Option 4: Alternative Pattern
- Recommend users pass indices or IDs instead of objects
- Use `format_func` for display
- Look up actual object separately
- Requires user education

## Impact Assessment

**Severity:** Medium
- Breaks specific use cases (singletons, identity-based logic)
- Has workarounds (pass indices instead of objects)
- Not affecting all users equally

**User Experience:** Negative
- Violates principle of least surprise
- Documentation doesn't match behavior
- Workarounds are non-obvious

**Maintenance:** Low-to-Medium
- Issue keeps being reported
- Team needs to respond/triage repeatedly
- Enhancement with no movement for years

## Recommendation

This requires team decision on:

1. **Is the deepcopy requirement absolute?** Can we explore alternatives?
2. **Should we update documentation** to match actual behavior?
3. **Should we provide an opt-out mechanism** for users who need identity preservation?
4. **Should #3703 and #12585 be linked** to avoid duplicate tracking?

## Next Steps

- [ ] Await team decision on whether to reconsider this as a bug
- [ ] If staying as enhancement: Update documentation to reflect copying behavior
- [ ] If reconsidering as bug: Explore technical solutions (optional copying, smart copying, etc.)
- [ ] Consider closing #12585 as duplicate of #3703 if no new action planned

---

**Created:** 2025-01-13  
**Status:** Pending team review  
**App URL:** https://issues.streamlitapp.com/gh-12585  
**Related Issues:** #3703 (original report from 2021)

