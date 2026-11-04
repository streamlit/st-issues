from __future__ import annotations

import streamlit as st

SELECTION_SHA_KEY = "perf_selected_commit_sha"
SELECTION_PAGE_KEY = "perf_selected_commit_page"
PER_CHART_SELECTION_PREFIX = "perf_selected_commit_chart_"
DEFAULT_COMMIT_URL_PREFIX = "https://github.com/streamlit/streamlit/commit/"


def update_selected_commit(shas: list[str], selection_key: str | None = None) -> None:
    """Store the commit selected in a chart and rerun so the sidebar shows it.

    ``shas`` are the commits of the currently selected chart points. When a
    chart keeps earlier points selected, the most recently added one wins.
    """
    shas = list(dict.fromkeys(sha for sha in shas if sha))
    if not shas:
        return

    selected_sha = shas[-1]
    if selection_key:
        state_key = f"{PER_CHART_SELECTION_PREFIX}{selection_key}"
        previous_shas = st.session_state.get(state_key, [])
        if previous_shas == shas:
            return
        if isinstance(previous_shas, list) and previous_shas:
            new_shas = [sha for sha in shas if sha not in previous_shas]
            if new_shas:
                selected_sha = new_shas[-1]
        st.session_state[state_key] = shas

    # Check if the selection actually changed before updating and rerunning
    current_sha = st.session_state.get(SELECTION_SHA_KEY)
    if current_sha == selected_sha:
        return

    st.session_state[SELECTION_SHA_KEY] = selected_sha
    # Force immediate rerun so the sidebar (rendered earlier in the script)
    # displays the newly selected commit SHA
    st.rerun()


def reset_selection_on_page_change(page_key: str) -> None:
    if st.session_state.get(SELECTION_PAGE_KEY) == page_key:
        return

    for key in list(st.session_state.keys()):
        if key == SELECTION_SHA_KEY:
            st.session_state.pop(key, None)
            continue
        if isinstance(key, str) and key.startswith(PER_CHART_SELECTION_PREFIX):
            st.session_state.pop(key, None)

    st.session_state[SELECTION_PAGE_KEY] = page_key


def render_selected_commit_sidebar() -> None:
    st.sidebar.subheader("Selected commit")

    selected_sha = st.session_state.get(SELECTION_SHA_KEY)
    if not selected_sha:
        st.sidebar.caption("Click a datapoint to view the commit SHA.")
        return

    st.sidebar.write(f"Short SHA: `{selected_sha[:7]}`")
    st.sidebar.markdown(f"[Open commit]({DEFAULT_COMMIT_URL_PREFIX}{selected_sha})")
