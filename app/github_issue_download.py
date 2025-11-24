from __future__ import annotations

import io
from typing import Dict, Iterable, List, Optional

import pandas as pd
import streamlit as st

from app.utils.github_utils import get_all_github_issues

st.set_page_config(
    page_title="Download GitHub Issues",
    page_icon="⬇️",
    initial_sidebar_state="collapsed",
)

st.title("Download GitHub Issues")
st.caption(
    "Export GitHub issues (excluding pull requests by default) with metadata and full "
    "issue bodies as a CSV file for offline analysis."
)


@st.cache_data(show_spinner=False)
def _fetch_issue_data(state: str) -> List[Dict[str, object]]:
    """Retrieve raw issue payloads for the configured repository."""
    return get_all_github_issues(state=state)


def _format_issue_record(
    issue: Dict[str, object],
    include_pull_requests: bool = False,
) -> Optional[Dict[str, object]]:
    """Transform a GitHub issue payload into a flat record suitable for CSV export."""
    if not include_pull_requests and "pull_request" in issue:
        return None

    user_info = issue.get("user") or {}
    milestone_info = issue.get("milestone") or {}
    reactions_info = issue.get("reactions") or {}
    assignees_info: Iterable[Dict[str, object]] = issue.get("assignees") or []
    labels_info: Iterable[Dict[str, object]] = issue.get("labels") or []

    labels = [
        str(label.get("name", "")).strip()
        for label in labels_info
        if isinstance(label, dict)
    ]

    assignees = [
        str(assignee.get("login", "")).strip()
        for assignee in assignees_info
        if isinstance(assignee, dict)
    ]

    body = issue.get("body")
    if body is None:
        body = ""

    record: Dict[str, object] = {
        "id": issue.get("id"),
        "node_id": issue.get("node_id"),
        "number": issue.get("number"),
        "title": issue.get("title"),
        "state": issue.get("state"),
        "author": user_info.get("login"),
        "author_id": user_info.get("id"),
        "author_association": issue.get("author_association"),
        "created_at": issue.get("created_at"),
        "updated_at": issue.get("updated_at"),
        "closed_at": issue.get("closed_at"),
        "labels": ", ".join(label for label in labels if label),
        "label_count": len(labels),
        "assignees": ", ".join(assignee for assignee in assignees if assignee),
        "assignee_count": len(assignees),
        "milestone": milestone_info.get("title") if milestone_info else None,
        "is_locked": issue.get("locked", False),
        "comments": issue.get("comments"),
        "reactions_total": reactions_info.get("total_count"),
        "html_url": issue.get("html_url"),
        "body": body,
        "body_length": len(body),
        "is_pull_request": "pull_request" in issue,
    }

    return record


if "issues_df" not in st.session_state:
    st.session_state["issues_df"] = None
if "issues_state" not in st.session_state:
    st.session_state["issues_state"] = "all"

with st.form("issue_download_form"):
    issue_state = st.selectbox(
        "Issue state",
        options=["open", "closed", "all"],
        index=["open", "closed", "all"].index(st.session_state["issues_state"]),
        help="GitHub issues state to fetch.",
    )
    include_prs = st.checkbox(
        "Include pull requests",
        value=False,
        help="GitHub exposes pull requests through the issues API; enable to include them.",
    )
    submit = st.form_submit_button("Load issues")

if submit:
    with st.spinner("Fetching issues from GitHub…"):
        raw_issues = _fetch_issue_data(issue_state)

    records: List[Dict[str, object]] = []
    for issue in raw_issues:
        record = _format_issue_record(issue, include_pull_requests=include_prs)
        if record:
            records.append(record)

    if not records:
        st.warning("No issues matched the selected criteria.")
        st.session_state["issues_df"] = None
    else:
        issues_df = pd.DataFrame.from_records(records)
        st.session_state["issues_df"] = issues_df
        st.session_state["issues_state"] = issue_state
        st.success(f"Loaded {len(records)} issues.")

issues_df: Optional[pd.DataFrame] = st.session_state.get("issues_df")
if issues_df is not None and not issues_df.empty:
    csv_buffer = io.StringIO()
    issues_df.to_csv(csv_buffer, index=False)

    st.download_button(
        label="Download issues as CSV",
        data=csv_buffer.getvalue(),
        file_name=f"github_issues_{st.session_state['issues_state']}.csv",
        mime="text/csv",
    )

    with st.expander("Preview (first 20 issues without body)"):
        preview_columns = [col for col in issues_df.columns if col not in {"body"}]
        st.dataframe(issues_df.loc[:, preview_columns].head(20), width="stretch")
