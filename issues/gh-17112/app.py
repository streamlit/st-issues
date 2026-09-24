"""
Reproduction for GitHub Issue #17112
Title: st.button lost callback from a fragment > dialog > fragment
URL: https://github.com/streamlit/streamlit/issues/17112

Expected: Clicking Increment in the nested fragment raises Count by 1.
Actual:   The button action is dropped — Count stays 0.
Reported version: 1.64.0 (first broken release: 1.62.0)
"""
import streamlit as st

st.title("Issue #17112: button in fragment > dialog > fragment")
st.info(
    "🔗 [View original issue](https://github.com/streamlit/streamlit/issues/17112)"
)

st.header("Issue Overview")
st.write(
    "**Expected:** Open the dialog, click Increment, Count becomes 1 "
    "(callback / fragment rerun fires)."
)
st.error(
    "**Actual (Bug, 1.62+):** Increment does nothing. Count stays 0. "
    "The inner fragment was evicted from storage after the opener fragment reran, "
    "so the click is dropped."
)

st.divider()

st.header("Bug Demonstration")
st.write(
    """
**Steps:**
1. Click **Open Counter**.
2. In the dialog, click **Increment**.
3. On Streamlit 1.62+, Count stays 0. On 1.61.1 and earlier it becomes 1.
"""
)

_COUNTER_KEY = "standalone_counter_value"

if _COUNTER_KEY not in st.session_state:
    st.session_state[_COUNTER_KEY] = 0


@st.fragment
def _render_button_in_dialog() -> None:
    st.metric("Count", st.session_state[_COUNTER_KEY])
    if st.button("Increment", key="standalone_increment_btn", type="primary"):
        st.session_state[_COUNTER_KEY] += 1
        st.rerun(scope="fragment")


@st.fragment
def _render_open_button() -> None:
    @st.dialog("Counter", width="small")
    def _open_dialog() -> None:
        _render_button_in_dialog()

    st.button("Open Counter", key="standalone_open_btn", on_click=_open_dialog)


_render_open_button()

st.divider()

st.header("Workaround")
st.write(
    "Open the dialog from the parent fragment **body**, not from `on_click`, "
    "so the dialog fragment is re-registered during the ancestor rerun and is "
    "not evicted as a stale descendant. You can also drop the extra inner "
    "`@st.fragment` — `@st.dialog` is already a fragment — but that alone is "
    "not enough if the dialog is still opened from a parent-fragment callback."
)
st.code(
    """
@st.fragment
def _render_open_button() -> None:
    @st.dialog("Counter", width="small")
    def _open_dialog() -> None:
        st.metric("Count", st.session_state[_COUNTER_KEY])
        if st.button("Increment", type="primary"):
            st.session_state[_COUNTER_KEY] += 1
            st.rerun(scope="fragment")

    if st.button("Open Counter"):
        st.session_state["show_counter"] = True
    if st.session_state.get("show_counter"):
        _open_dialog()
""".strip(),
    language="python",
)

st.divider()

st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
