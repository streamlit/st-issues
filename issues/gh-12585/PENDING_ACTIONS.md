# Pending Actions for Issue #12585

## Status: Awaiting Decisions

This issue has been analyzed and requires team decisions before proceeding with confirmation or closure.

## Pending Action Items

### 1. Documentation Issue ⏸️ **AWAITING DOCS MAINTAINER RESPONSE**

**Issue:** The `st.selectbox` documentation is misleading.

**Current Documentation:**
> "Returns: The selected option or None if no option is selected."

**Actual Behavior:**
> Returns a **copy** of the selected option (deepcopy), not the original object

**Action Needed:**
- Create a documentation issue to clarify that `st.selectbox` returns copies of objects
- Waiting for docs maintainer to confirm preferred process for creating docs issues

**Details:**
- This affects users working with object identity (singletons, caching, etc.)
- Users reasonably expect object identity to be preserved based on current docs
- Documentation should either:
  - State that copies are returned
  - Add guidance on working with object identity
  - Explain workarounds (using indices instead of objects)

### 2. Relationship to Issue #3703 🔗

**Decision Needed:** Should this be closed as duplicate?

**Context:**
- Issue #3703 (2021) reported the exact same problem
- #3703 was converted to `type:enhancement` in 2023 by @jrieke
- #3703 is still open with no progress for 4+ years

**Considerations:**
- #12585 adds minimal new technical information
- Main addition: documentation discrepancy point
- Issue reporter acknowledged they're "re-upping" the old bug

**Options:**
1. Close #12585 as duplicate of #3703
2. Keep both open and link them
3. Close #3703 and use #12585 as the primary tracker
4. Reconsider the "enhancement" classification and treat as bug

### 3. Team Decision Required 🤔

**Core Question:** Is this a bug or expected behavior?

**Historical Context:**
- Was a **regression** in Streamlit 0.84 (worked in 0.83)
- Team explained deepcopy needed for session_state callback mechanisms
- Marked as "enhancement" (expected behavior) in 2023
- No progress in 2+ years since

**Team Needs to Decide:**
- Should this be reconsidered as a bug given documentation discrepancy?
- Is there appetite to add opt-out mechanism for copying?
- Should we just fix documentation and keep as expected behavior?

## Current State

- ✅ Reproduction app created: https://issues.streamlitapp.com/gh-12585
- ✅ NOTES.md created with full analysis
- ✅ Confirmed issue reproduces even with session_state persisted objects
- ⏸️ No comment posted on issue yet (awaiting decisions)
- ⏸️ Labels not updated yet (awaiting decisions)

## Next Steps

1. **Wait for docs maintainer response** on process for creating docs issue
2. **Create docs issue** once process confirmed
3. **Post comment on #12585** explaining:
   - Link to reproduction app
   - Relationship to #3703
   - Documentation discrepancy
   - Ask team for decision on bug vs enhancement
   - Link to docs issue once created
4. **Update labels** based on team decision:
   - If reconsidering as bug: `status:awaiting-team-response`
   - If closing as duplicate: close with link to #3703
   - If keeping as enhancement: add appropriate labels

## References

- **This Issue:** https://github.com/streamlit/streamlit/issues/12585
- **Original Issue (2021):** https://github.com/streamlit/streamlit/issues/3703
- **Reproduction App:** https://issues.streamlitapp.com/gh-12585
- **Analysis:** `NOTES.md` in this folder

---

**Created:** 2025-01-13  
**Last Updated:** 2025-01-13  
**Status:** Awaiting docs process confirmation

