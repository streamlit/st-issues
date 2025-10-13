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

## The Key Pattern Workaround

### Always Available Solution

There is a clean workaround that works for **all** cases where object identity matters:

**Instead of passing objects, pass keys:**

```python
# Store objects in session_state
if 'prod_db' not in st.session_state:
    st.session_state.prod_db = DatabaseConnection("Production", "...")
    st.session_state.dev_db = DatabaseConnection("Development", "...")

# Select by key, not object
selected_key = st.selectbox(
    "Select Database",
    ["prod_db", "dev_db"],
    format_func=lambda key: st.session_state[key].name  # Display name
)

# Get the actual object
selected_db = st.session_state[selected_key]

# Now you have the actual singleton with preserved identity
if selected_db is st.session_state.prod_db:  # Works!
    enable_prod_logging()
```

### Why This Workaround Is Always Available

**Critical Insight:** If object identity matters across reruns, objects MUST be stored in `st.session_state`. And if they're in session_state, they already have keys.

**Logic:**
1. Object identity only matters if objects persist across reruns
2. Persisting across reruns requires `st.session_state`
3. `st.session_state` uses string keys to store objects
4. Therefore, you always have keys available to use

**Conclusion:** There is no scenario where you need object identity but can't use the key pattern.

### Why This Pattern Is Actually Better

1. **More explicit:** Clear that you're selecting an identifier
2. **Lighter weight:** No need to serialize/copy entire objects
3. **Works with Streamlit's architecture:** Aligns with rerun model
4. **Standard pattern:** Similar to database lookups (select by ID)
5. **No ambiguity:** Clear separation between selection and object access

## Revised Assessment

Given the key pattern workaround is always available and actually a better design:

### This Is Correctly An Enhancement, Not A Bug

**Reasons:**
1. **No blocking use case:** Every scenario has a clean workaround
2. **Workaround is simple:** One extra line to look up by key
3. **Workaround is better design:** More explicit and Streamlit-friendly
4. **Deepcopy serves a purpose:** Protects session_state callbacks
5. **Would break backward compatibility:** Changing this could break existing apps

### The Real Problem Is Documentation

The issue is not the copying behavior itself, but that:
1. Docs don't mention copying happens
2. Docs don't show the key pattern for objects
3. Users aren't guided to the better pattern

## Possible Solutions

### Option 1: Accept As Expected, Fix Documentation ✅ **RECOMMENDED**

- Update docs to clearly state selectbox returns copies
- Add guidance on using keys when object identity matters
- Show key pattern in examples with session_state objects
- Minimal code changes, maximum benefit

### Option 2: Make Copying Optional

- Add parameter like `copy_selection=True` (default for backward compatibility)
- Allow users to opt out when they need identity preservation
- Requires API change, maintenance burden
- **Not recommended:** Workaround is sufficient and actually better design

### Option 3: Smart Copying

- Only deepcopy when necessary (e.g., when callbacks are involved)
- Use shallow copy or no copy when safe
- Requires careful implementation, potential edge cases
- **Not recommended:** Complex with limited benefit given workaround exists

### Option 4: Close as duplicate of #3703

- Same technical issue, same assessment applies
- No new blocking information provided
- Reduces duplicate tracking overhead
- **Recommended:** Along with documentation fix

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

Based on the analysis, the recommended path forward is:

### 1. Keep as Enhancement (Correctly Classified) ✅

- Copying behavior serves a purpose (session_state callbacks)
- Clean workaround exists for all use cases
- Workaround is actually better design pattern
- No blocking scenarios identified

### 2. Fix Documentation (Primary Action Item) 📝

**What to add to st.selectbox docs:**
- Clarify that selected options are returned as copies (deepcopy)
- Explain why (protects session_state mechanisms)
- Show the key pattern for when object identity matters:
  ```python
  # When you need object identity, use keys
  selected_key = st.selectbox("Choose", ["key1", "key2"])
  selected_object = st.session_state[selected_key]
  ```
- Recommend this pattern for complex objects

### 3. Close #12585 as Duplicate of #3703 🔗

- Same technical issue
- No new blocking information
- #3703 already correctly classified as enhancement
- Reduces maintenance overhead

## Next Steps

- [ ] Wait for docs maintainer to confirm process for docs issues
- [ ] Create documentation issue with specific recommendations
- [ ] Comment on #12585 explaining:
  - Link to reproduction app
  - Key pattern workaround (always available)
  - Relationship to #3703
  - Recommendation to close as duplicate
  - Link to docs issue
- [ ] Close #12585 as duplicate of #3703 with appropriate links

---

**Created:** 2025-01-13
**Status:** Pending team review
**App URL:** https://issues.streamlitapp.com/gh-12585
**Related Issues:** #3703 (original report from 2021)
