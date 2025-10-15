# Issue #12782 - Technical Analysis

## Issue Summary

**Regression in 1.50.0:** `st.multiselect` ignores `default` values when:
1. Widget is inside `@st.fragment`
2. Parent widget has `on_change` that clears the **widget's session state key**
3. The `default` parameter references a **different** session state key
4. This is a common pattern for managing defaults separately from widget state

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
    options=conversation_ids,
    default=st.session_state.selected_conversation,  # Different key
    key=_key,  # Widget key
    ...
)
```

**The pattern:**
- Default source: `st.session_state.selected_conversation`
- Widget key: `_key` (e.g., "conversation_multiselect")
- These are **different** keys
- When parent's `on_change` clears the widget key, the `default` should take effect
- But in 1.50.0, it doesn't

## Reproduction Strategy

The reproduction app attempts to trigger this by:

1. **Separate keys for defaults vs widget state:**
   - `saved_conversation_defaults` - stores the intended default values
   - `conversation_multiselect` - the widget's actual key

2. **Parent with on_change that clears widget key:**
   - Selectbox for patient selection
   - `on_change` callback deletes `st.session_state["conversation_multiselect"]`
   - Does NOT delete `saved_conversation_defaults`

3. **Fragment re-execution:**
   - Fragment contains the multiselect
   - After parent change, fragment re-runs
   - Multiselect should pick up default from `saved_conversation_defaults`
   - But in 1.50.0, it may show empty instead

## Potential Root Causes

### Hypothesis 1: Widget Registration Timing
In fragments with on_change callbacks that modify session state, the timing of when:
- The callback executes
- Session state is synchronized
- Widget default values are evaluated
- May have changed in 1.50.0

### Hypothesis 2: Default Parameter Resolution
The `default` parameter resolution might have changed to:
- Only look at the widget's own key first
- Not properly fall back to the provided `default` value
- When the widget key doesn't exist after being deleted

### Hypothesis 3: Fragment State Synchronization
Fragments may have changed how they synchronize session state between:
- The parent script's state changes (from on_change)
- The fragment's re-execution context

## Code Investigation Points

Looking at `lib/streamlit/elements/widgets/multiselect.py`:

```python
# Lines 558-560
if widget_state.value_changed:
    proto.raw_values[:] = serde.serialize(widget_state.value)
    proto.set_value = True
```

This only sets `proto.set_value = True` when `value_changed` is True.

**Question:** After a key is deleted by on_change, does the widget registration in fragments properly recognize that it should use the default value? Or does `value_changed` incorrectly remain False, preventing the default from being applied?

## Testing Protocol

To verify the bug:

1. **Setup:** Deploy to 1.50.0 environment
2. **Step 1:** Select "Patient A" - multiselect should show first conversation
3. **Step 2:** Optionally change multiselect selection
4. **Step 3:** Change to "Patient B"
5. **Expected:** Multiselect shows first conversation of Patient B (from `saved_conversation_defaults`)
6. **Bug (if present):** Multiselect is empty despite `saved_conversation_defaults` having values

## Workaround Confirmation

The workaround explicitly syncs keys:
```python
st.session_state[widget_key] = st.session_state[defaults_key]
```

This forces the widget to have a value in its own key, bypassing the need for the `default` parameter to work correctly.

## Related Changes to Investigate

Check git history between 1.49.1 and 1.50.0 for changes to:
- `streamlit/runtime/state/` - Widget state management
- `streamlit/elements/lib/fragment_utils.py` or fragment-related code
- `streamlit/elements/widgets/multiselect.py` - Widget registration logic
- Any changes to how `default` parameter is processed when widget key doesn't exist

## Difficulty Level

⚠️ **COMPLEX** - Reporter couldn't create minimal reproduction themselves, suggesting:
- Specific timing or state synchronization issue
- May only occur with exact combination of: fragment + on_change + separate state keys
- Requires specific Streamlit version (1.50.0) to reproduce

