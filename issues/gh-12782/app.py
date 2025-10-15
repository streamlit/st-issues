"""
Reproduction for GitHub Issue #12782
Title: Multiselect default values not respected in @st.fragment with on_change and session state logic (regression in 1.50.0)
Issue URL: https://github.com/streamlit/streamlit/issues/12782

Description:
This app reproduces a regression in Streamlit 1.50.0 where st.multiselect ignores default
values from session state when used inside a @st.fragment with on_change callbacks.

The key pattern: The multiselect's default comes from a DIFFERENT session state key than
the widget's key itself, and the parent's on_change clears the widget key.

Expected Behavior:
When a parent selector changes and clears the widget's session state key, the multiselect
should reinitialize with the default value from a separate session state key.

Actual Behavior (1.50.0):
The multiselect shows empty even though the separate session state key contains the correct
default value.
"""

import streamlit as st

st.title("Issue #12782: Multiselect Default in Fragment")

st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/12782)")

st.header("Issue Overview")
st.markdown("""
**Regression in 1.50.0:** `st.multiselect` default values are not respected when:
- Widget is inside `@st.fragment`
- Parent widget has `on_change` callback that clears the **widget's key**
- Multiselect uses `default` from a **different** session state key
- This is a common pattern for managing defaults separately from widget state

**Worked in:** 1.49.1
**Broken in:** 1.50.0
""")

st.divider()

# Data for different patients
PATIENT_CONVERSATIONS = {
    "": [],
    "Patient A": ["Initial Consultation", "Follow-up Visit", "Lab Results"],
    "Patient B": ["Emergency Visit", "Surgery Consultation", "Post-op Review"],
    "Patient C": ["Annual Checkup", "Vaccination", "Prescription Renewal"],
}


def reset_widget_key():
    """Callback when patient changes - clears THE WIDGET KEY (not the defaults key)"""
    # This is the key pattern - we clear the widget key but NOT the defaults key
    if "conversation_multiselect" in st.session_state:
        del st.session_state["conversation_multiselect"]
        st.toast("🗑️ Cleared widget key 'conversation_multiselect'")


@st.fragment
def conversation_selector():
    """Fragment containing the multiselect that exhibits the bug"""

    # Get current patient and their conversations
    patient = st.session_state.get("patient", "")
    conversations = PATIENT_CONVERSATIONS.get(patient, [])

    st.subheader("📋 Conversation Selector (Inside Fragment)")

    if not conversations:
        st.warning("No conversations found. Please select a patient first.")
        return

    # KEY PATTERN: We manage defaults in a SEPARATE session state key
    # This is common for preserving user's last selection across parent changes
    if "saved_conversation_defaults" not in st.session_state:
        st.session_state.saved_conversation_defaults = [conversations[0]]
    else:
        # Update defaults if the current defaults aren't in the new options
        if not all(c in conversations for c in st.session_state.saved_conversation_defaults):
            st.session_state.saved_conversation_defaults = [conversations[0]]

    # Display session state BEFORE multiselect
    st.code(
        f"Default source key: {st.session_state.saved_conversation_defaults}",
        language="python",
    )
    st.code(
        f"Widget key: {st.session_state.get('conversation_multiselect', 'NOT SET')}",
        language="python",
    )

    # The problematic multiselect
    # KEY: default comes from 'saved_conversation_defaults' but widget key is 'conversation_multiselect'
    st.markdown("**🐛 Bug Demonstration:**")
    st.caption("Widget key: `conversation_multiselect`, Default from: `saved_conversation_defaults`")

    selected = st.multiselect(
        label="Select conversations",
        options=conversations,
        default=st.session_state.saved_conversation_defaults,  # Different key!
        key="conversation_multiselect",  # Widget key
        help="BUG: After parent change, this ignores the default from saved_conversation_defaults",
    )

    # Update the saved defaults based on user selection
    if selected:
        st.session_state.saved_conversation_defaults = selected

    # Display what was actually selected
    st.code(f"Actually selected: {selected}", language="python")

    # Show the problem
    if not selected and st.session_state.saved_conversation_defaults:
        st.error("❌ BUG REPRODUCED!")
        st.write("- Multiselect is empty")
        st.write(f"- But `saved_conversation_defaults` has: {st.session_state.saved_conversation_defaults}")
        st.write("- The `default` parameter is being ignored!")
    elif selected:
        st.success("✅ Multiselect has values (bug not visible or fixed)")


st.header("Reproduction Steps")

st.markdown("""
1. Select a patient from the dropdown below
2. Notice the multiselect initializes with the first conversation
3. **Optionally:** Change your selection in the multiselect
4. **Change to a different patient**
5. Observe what happens:
   - **Expected (1.49.1):** Multiselect reinitializes with default from `saved_conversation_defaults`
   - **Bug (1.50.0):** Multiselect shows empty even though `saved_conversation_defaults` has values
   
**Why this happens:**
- The `on_change` callback clears the widget's key (`conversation_multiselect`)
- The `default` parameter should fallback to `saved_conversation_defaults`
- But in 1.50.0, the default is ignored after the widget key is cleared
""")

# Parent selector with on_change callback
st.selectbox(
    "Select Patient",
    options=list(PATIENT_CONVERSATIONS.keys()),
    key="patient",
    on_change=reset_widget_key,
    help="Changing this will clear the widget key via on_change callback",
)

# Fragment with the problematic multiselect
conversation_selector()

st.divider()

st.header("Workaround")
st.markdown("""
The reporter found that **explicitly setting the widget key** in session state before rendering fixes the issue:

```python
# Workaround for 1.50.0
# Explicitly sync the widget key with the defaults key
st.session_state["conversation_multiselect"] = st.session_state.saved_conversation_defaults

selected = st.multiselect(
    label="Select conversations",
    options=conversations,
    default=st.session_state.saved_conversation_defaults,
    key="conversation_multiselect"
)
```

This forces the widget to pick up the value even when the `default` parameter isn't being respected.
""")

# Demonstrate the workaround
if st.session_state.get("patient"):
    st.subheader("✅ Workaround Example")

    @st.fragment
    def conversation_selector_with_workaround():
        patient = st.session_state.get("patient", "")
        conversations = PATIENT_CONVERSATIONS.get(patient, [])

        if not conversations:
            return

        # Manage defaults in separate key (same pattern as bug demo)
        if "saved_defaults_workaround" not in st.session_state:
            st.session_state.saved_defaults_workaround = [conversations[0]]
        else:
            if not all(c in conversations for c in st.session_state.saved_defaults_workaround):
                st.session_state.saved_defaults_workaround = [conversations[0]]

        # WORKAROUND: Explicitly set the widget key before rendering
        st.session_state["multiselect_workaround"] = (
            st.session_state.saved_defaults_workaround
        )

        selected = st.multiselect(
            label="Select conversations (with workaround)",
            options=conversations,
            default=st.session_state.saved_defaults_workaround,
            key="multiselect_workaround",
            help="This should work even in 1.50.0 due to the workaround",
        )

        # Update saved defaults
        if selected:
            st.session_state.saved_defaults_workaround = selected

        st.code(f"Selected: {selected}", language="python")

        if selected:
            st.success("✅ Workaround: Defaults loaded correctly")

    conversation_selector_with_workaround()

st.divider()

st.header("Environment Info")
st.code(f"""
Streamlit version: {st.__version__}
Python version: 3.12+
Affected versions: 1.50.0
Working versions: 1.49.1
""")

st.header("Technical Details")
st.markdown("""
**Root cause (speculation):**
- Fragment re-execution timing may have changed in 1.50.0
- Widget default initialization might occur before session state is properly synchronized
- The workaround (explicitly setting the widget key) forces synchronization before rendering

**Key components involved:**
- `@st.fragment` decorator
- `st.multiselect` with `default` parameter from session state
- Parent widget with `on_change` callback that modifies session state
- Session state re-initialization after parent change
""")
