from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


def segmented_tabs(
    *,
    options: Sequence[str],
    key: str,
    query_param: str = "tab",
    default: str | None = None,
    label: str = "Tab",
) -> str:
    """Render a segmented-control tab switcher and persist the selection.

    Persists the selection in:
    - st.session_state[key]
    - st.query_params[query_param].

    Returns the selected option (always one of `options`).
    """
    if not options:
        msg = "segmented_tabs: `options` must not be empty"
        raise ValueError(msg)

    options_list = list(options)
    default_value = default if default in options_list else options_list[0]

    qp_value = st.query_params.get(query_param)
    if isinstance(qp_value, str) and qp_value in options_list:
        default_value = qp_value

    selected = st.segmented_control(
        label,
        options=options_list,
        default=default_value,
        key=key,
        width="stretch",
        label_visibility="collapsed",
    )

    # st.segmented_control may return None in some edge cases; normalize.
    selected = selected if selected in options_list else default_value

    # Keep the URL in sync (shareable links like ?tab=Explorer).
    if st.query_params.get(query_param) != selected:
        st.query_params[query_param] = selected

    return selected


def ensure_one_of(value: str | None, allowed: Iterable[str], fallback: str) -> str:
    allowed_set = set(allowed)
    return value if value in allowed_set else fallback
