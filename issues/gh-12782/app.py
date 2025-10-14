"""
Reproduction for GitHub Issue #12782
Title: Multiselect default values not respected in @st.fragment with on_change and session state logic (regression in 1.50.0)
Issue URL: https://github.com/streamlit/streamlit/issues/12782

Description:
This app reproduces a regression in Streamlit 1.50.0 where st.multiselect ignores default 
values from session state when used inside a @st.fragment with on_change callbacks.

Expected Behavior:
When a parent selector changes and clears multiselect session state, the multiselect should 
reinitialize with the default value from session state.

Actual Behavior (1.50.0):
The multiselect shows empty even though the session state contains the correct default value.
"""

import streamlit as st

st.title("Issue #12782: Multiselect Default in Fragment")

st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/12782)")

st.header("Issue Overview")
st.markdown("""
**Regression in 1.50.0:** `st.multiselect` default values are not respected when:
- Widget is inside `@st.fragment`
- Parent widget has `on_change` callback that clears state
- Multiselect uses session state for default values

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


def reset_conversation_selection():
    """Callback when patient changes - clears conversation selection"""
    if "selected_conversations" in st.session_state:
        del st.session_state["selected_conversations"]
    st.toast(f"Cleared conversation selection for patient change")


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
    
    # Initialize default selection (always select first conversation)
    if "selected_conversations" not in st.session_state:
        st.session_state.selected_conversations = [conversations[0]]
    
    # Display session state BEFORE multiselect
    st.code(f"Session state default: {st.session_state.selected_conversations}", language="python")
    
    # The problematic multiselect
    st.markdown("**🐛 Bug Demonstration:**")
    selected = st.multiselect(
        label="Select conversations",
        options=conversations,
        default=st.session_state.selected_conversations,
        key="conversation_multiselect",
        help="In 1.50.0, this will show empty after patient change despite session state having defaults"
    )
    
    # Display what was actually selected
    st.code(f"Actually selected: {selected}", language="python")
    
    # Show the problem
    if not selected and st.session_state.selected_conversations:
        st.error("❌ BUG: Multiselect is empty but session state has defaults!")
        st.write("This is the bug - the default values are being ignored.")
    elif selected == st.session_state.selected_conversations:
        st.success("✅ Expected behavior: Defaults are properly loaded")


st.header("Reproduction Steps")

st.markdown("""
1. Select a patient from the dropdown below
2. Notice the multiselect initializes with the first conversation (correct in both versions)
3. **Change to a different patient**
4. Observe what happens:
   - **1.49.1 (expected):** Multiselect reinitializes with the first conversation of the new patient
   - **1.50.0 (bug):** Multiselect shows empty even though session state has the default
""")

# Parent selector with on_change callback
st.selectbox(
    "Select Patient",
    options=list(PATIENT_CONVERSATIONS.keys()),
    key="patient",
    on_change=reset_conversation_selection,
    help="Changing this will clear the conversation selection via on_change callback"
)

# Fragment with the problematic multiselect
conversation_selector()

st.divider()

st.header("Workaround")
st.markdown("""
The reporter found that explicitly setting the widget key in session state before rendering fixes the issue:

```python
# Workaround for 1.50.0
st.session_state["conversation_multiselect"] = st.session_state.selected_conversations

selected = st.multiselect(
    label="Select conversations",
    options=conversations,
    default=st.session_state.selected_conversations,
    key="conversation_multiselect"
)
```
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
        
        if "selected_conversations_workaround" not in st.session_state:
            st.session_state.selected_conversations_workaround = [conversations[0]]
        
        # WORKAROUND: Explicitly set the key
        st.session_state["conversation_multiselect_workaround"] = st.session_state.selected_conversations_workaround
        
        selected = st.multiselect(
            label="Select conversations (with workaround)",
            options=conversations,
            default=st.session_state.selected_conversations_workaround,
            key="conversation_multiselect_workaround",
            help="This should work even in 1.50.0 due to the workaround"
        )
        
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

