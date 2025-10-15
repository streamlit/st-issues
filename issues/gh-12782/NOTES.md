# Issue #12782 - Technical Analysis

## Issue Summary

**Regression in 1.50.0:** `st.multiselect` ignores `default` values when:

1. Widget is inside `@st.fragment`
2. Parent widget changes, causing the **options** to change
3. Widget key persists but contains values from OLD options (now invalid)
4. The `default` parameter references a **different** session state key
5. The "key as main identity" logic should detect options changed and use defaults
6. But the default from the separate key may not be respected

**Key insight:** This is likely related to the `key_as_main_identity` feature that includes `"options"` in the identity computation (see multiselect.py lines 501-506).

## Reporter's Context

The reporter specifically noted:

- "Unfortunately, I couldn't reproduce the issue in a minimal code snippet"
- Issue occurs in complex interaction between fragments, nested state logic, and conditional UI
- The workaround is: `st.session_state[_key] = st.session_state.selected_conversation`
- This explicitly syncs the widget key with the defaults key before rendering

## Key Pattern Identified

Looking at the reporter's code snippet:

```python
if "selected_conversation" not in st.session_state:
    st.session_state.selected_conversation = _saved_conversations

# BUG: This line shouldn't be needed but is required in 1.50.0
st.session_state[_key] = st.session_state.selected_conversation

_related_conversations = st.multiselect(
    label="Select **conversations**",
    options=conversation_ids,  # Changes when parent changes
    default=st.session_state.selected_conversation,  # Different key
    key=_key,  # Widget key (persists with old values)
    ...
)
```

**The actual pattern:**

- Default source: `st.session_state.selected_conversation`
- Widget key: `_key` (e.g., "conversation_multiselect")
- These are **different** keys
- When parent changes, the **options change** (new patient = new conversation list)
- Widget key still exists but references OLD options
- The `key_as_main_identity` logic should invalidate the old selection
- Then it should fall back to the `default` parameter
- But in 1.50.0, it doesn't

**Initial hypothesis was wrong:** The on_change callback doesn't necessarily clear the widget key. Instead, the widget key persists with old values, and the bug is about what happens when options change.

## Reproduction Strategy (Updated)

The reproduction app attempts to trigger this by:

1. **Separate keys for defaults vs widget state:**

   - `saved_conversation_defaults` - stores the intended default values
   - `conversation_multiselect` - the widget's actual key (persists between parent changes)

2. **Parent that causes options to change:**

   - Selectbox for patient selection
   - When changed, the fragment re-renders with NEW options
   - Widget key still has OLD values (from previous patient's conversations)

3. **Fragment re-execution:**
   - Fragment contains the multiselect
   - After parent change, fragment re-runs with NEW options
   - Widget key contains values that don't exist in new options
   - `key_as_main_identity` should detect options changed
   - Should invalidate old selection and use `default` from `saved_conversation_defaults`
   - But in 1.50.0, it may show empty instead

## Potential Root Causes

### Hypothesis 1: key_as_main_identity with Fragments

The `key_as_main_identity` feature in 1.50.0 includes options in the identity:

```python
# multiselect.py lines 494-516
element_id = compute_and_register_element_id(
    widget_name,
    user_key=key,
    # Treat the provided key as the main identity. Only include
    # changes to the options, accept_new_options, and max_selections
    # in the identity computation as those can invalidate the
    # current selection.
    key_as_main_identity={
        "options",
        "max_selections",
        "accept_new_options",
        "format_func",
    },
    ...
)
```

**Potential issue:** In fragments, when options change:

- The element_id computation detects the change
- This should trigger widget state invalidation
- Then fall back to the `default` parameter
- But in fragments, the default parameter resolution might not work correctly

### Hypothesis 2: Widget Registration Timing in Fragments

After options change and widget state is invalidated:

- The widget registration should look at the `default` parameter
- But in fragments, there might be a timing issue where:
  - The old widget state is cleared
  - But the `default` parameter isn't properly evaluated
  - Resulting in an empty widget

### Hypothesis 3: Default Parameter vs Widget Value Priority

When widget key exists but is invalidated due to options change:

- Should: Clear widget value, use default parameter
- Bug: Widget value is cleared but default parameter is also ignored
- Result: Empty widget

## Code Investigation Points

Looking at `lib/streamlit/elements/widgets/multiselect.py`:

```python
# Lines 558-560
if widget_state.value_changed:
    proto.raw_values[:] = serde.serialize(widget_state.value)
    proto.set_value = True
```

**Questions:**

1. After `key_as_main_identity` detects options changed, how is the widget state updated?
2. Does `widget_state.value_changed` properly reflect that defaults should be used?
3. In fragments, is there a special code path that affects default handling?

## Testing Protocol

To verify the bug:

1. **Setup:** Deploy to 1.50.0 environment
2. **Step 1:** Select "Patient A" - multiselect should show first conversation
3. **Step 2:** Optionally change multiselect selection to something else
4. **Step 3:** Change to "Patient B"
5. **Debug info should show:**
   - Current options: ["Emergency Visit", "Surgery Consultation", "Post-op Review"]
   - saved_conversation_defaults: ["Emergency Visit"]
   - Widget key: ["Initial Consultation"] or similar (FROM OLD OPTIONS!)
6. **Expected:** Multiselect shows "Emergency Visit" (from `saved_conversation_defaults`)
7. **Bug (if present):** Multiselect is empty despite `saved_conversation_defaults` having values

## Workaround Confirmation

The workaround explicitly syncs keys BEFORE the widget renders:

```python
st.session_state[widget_key] = st.session_state[defaults_key]
```

This ensures the widget key has the correct value, bypassing the need for:

1. Options change detection
2. Widget state invalidation
3. Default parameter fallback

## Related Changes to Investigate

Check git history between 1.49.1 and 1.50.0 for changes to:

- `streamlit/elements/lib/utils.py` - `compute_and_register_element_id` with `key_as_main_identity`
- `streamlit/runtime/state/` - Widget state management after invalidation
- Fragment-related code - How fragments handle widget state changes
- `streamlit/elements/widgets/multiselect.py` - Default parameter resolution

**Specific focus:** Look for changes related to `key_as_main_identity` feature introduction.

## Difficulty Level

⚠️ **COMPLEX** - Reporter couldn't create minimal reproduction themselves, suggesting:

- Specific combination required: fragment + options change + separate state keys
- Related to recent `key_as_main_identity` feature (1.50.0 change)
- May require specific Streamlit version (1.50.0) to reproduce
- Timing/state synchronization issue in fragments

## Additional Notes

The key realization from the team member review:

> "if we DON'T clear the widget key if we will be able to reproduce it. This is consistent with the recent changes to support 'key as main identity'"

This insight shifted the reproduction strategy from:

- ❌ Clearing widget key via on_change
- ✅ Letting widget key persist with old values while options change
