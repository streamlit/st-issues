from __future__ import annotations

from typing import Any

import streamlit as st

SELECTION_SHA_KEY = "perf_selected_commit_sha"
SELECTION_PAGE_KEY = "perf_selected_commit_page"
PER_CHART_SELECTION_PREFIX = "perf_selected_commit_chart_"
DEFAULT_COMMIT_URL_PREFIX = "https://github.com/streamlit/streamlit/commit/"


def _normalize_selection_payload(selection: Any) -> dict[str, Any] | None:
    if selection is None:
        return None

    if hasattr(selection, "selection"):
        selection = selection.selection
    elif hasattr(selection, "selected_data"):
        selection = selection.selected_data

    if isinstance(selection, dict):
        payload = selection.get("selection", selection)
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, list):
            return {"points": payload}
        return None

    if isinstance(selection, list):
        return {"points": selection}

    return None


def _extract_sha_from_point(point: dict[str, Any], sha_field: str) -> str | None:
    if sha_field in point and isinstance(point[sha_field], str):
        return point[sha_field]

    custom_data = point.get("customdata")
    if isinstance(custom_data, str):
        return custom_data
    if isinstance(custom_data, (list, tuple)):
        for entry in custom_data:
            if isinstance(entry, str):
                return entry
            if isinstance(entry, dict) and sha_field in entry and isinstance(entry[sha_field], str):
                return entry[sha_field]

    datum = point.get("datum")
    if isinstance(datum, dict) and isinstance(datum.get(sha_field), str):
        return datum[sha_field]

    return None


def extract_selected_commit_shas(selection: Any, sha_field: str = "commit_sha_full") -> list[str]:
    payload = _normalize_selection_payload(selection)
    if not payload:
        return []

    points = payload.get("points")
    if not isinstance(points, list):
        return []

    shas: list[str] = []
    for point in points:
        if not isinstance(point, dict):
            continue
        sha = _extract_sha_from_point(point, sha_field)
        if sha and sha not in shas:
            shas.append(sha)

    return shas


def update_selected_commit_from_selection(
    selection: Any,
    sha_field: str = "commit_sha_full",
    selection_key: str | None = None,
) -> None:
    shas = extract_selected_commit_shas(selection, sha_field=sha_field)
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
        if key == SELECTION_SHA_KEY or key.startswith(PER_CHART_SELECTION_PREFIX):
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
