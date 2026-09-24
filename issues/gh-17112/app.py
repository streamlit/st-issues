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
    "so the click is dropped. Fixed on develop by "
    "[#17039](https://github.com/streamlit/streamlit/pull/17039); still broken on 1.64.0."
)

st.divider()

st.header("Bug Demonstration")
st.write(
    """
**Steps:**
1. Click **Open Counter**.
2. In the dialog, click **Increment**.
3. On Streamlit 1.62+, Count stays 0. On 1.61.1, earlier, and current `develop`, it becomes 1.
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
    "not evicted as a stale descendant. Try **Open workaround dialog** below "
    "on 1.62–1.64: Increment should work."
)
st.success(
    "Workaround: set a session-state flag in the button click, then call the "
    "dialog function during the fragment body."
)

_WORKAROUND_COUNTER_KEY = "workaround_counter_value"
_SHOW_WORKAROUND_KEY = "show_workaround_counter"

if _WORKAROUND_COUNTER_KEY not in st.session_state:
    st.session_state[_WORKAROUND_COUNTER_KEY] = 0


@st.fragment
def _workaround_button_in_dialog() -> None:
    st.metric("Count (workaround)", st.session_state[_WORKAROUND_COUNTER_KEY])
    if st.button("Increment", key="workaround_increment_btn", type="primary"):
        st.session_state[_WORKAROUND_COUNTER_KEY] += 1
        st.rerun(scope="fragment")


@st.fragment
def _workaround_open_button() -> None:
    @st.dialog("Counter (workaround)", width="small")
    def _open_dialog() -> None:
        _workaround_button_in_dialog()

    if st.button("Open workaround dialog", key="workaround_open_btn"):
        st.session_state[_SHOW_WORKAROUND_KEY] = True
    if st.session_state.get(_SHOW_WORKAROUND_KEY):
        _open_dialog()


_workaround_open_button()

st.code(
    """
@st.fragment
def counter_dialog():
    @st.dialog("Counter", width="small")
    def _open_dialog():
        if "count" not in st.session_state:
            st.session_state.count = 0
        st.metric("Count", st.session_state.count)
        if st.button("Increment", type="primary"):
            st.session_state.count += 1
            st.rerun(scope="fragment")

    # Open from the fragment body, not on_click.
    if st.button("Open Counter"):
        st.session_state.show_counter = True
    if st.session_state.get("show_counter"):
        _open_dialog()


counter_dialog()
""".strip(),
    language="python",
)

st.divider()

st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
