from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional, Tuple

import requests
import streamlit as st
import yaml

st.set_page_config(page_title="Issue Exporter", page_icon="📤", layout="wide")
st.title("📤 GitHub Issue Exporter")
st.caption("Export issues from the streamlit/streamlit repository to a YAML file.")


# Function to fetch GitHub issues, adapted from other pages
@st.cache_data(ttl=60 * 60 * 12)  # cache for 12 hours
def get_all_github_issues(
    state: Literal["open", "closed", "all"] = "all",
    repo_owner: str = "streamlit",
    repo_name: str = "streamlit",
) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    page = 1
    headers = {}
    if "github" in st.secrets and "token" in st.secrets["github"]:
        headers["Authorization"] = "token " + st.secrets["github"]["token"]
    else:
        st.warning(
            "GitHub token not found in st.secrets. API calls might be rate-limited or fail for private repos."
        )

    state_param = f"state={state}"

    while True:
        try:
            response = requests.get(
                f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues?{state_param}&per_page=100&page={page}",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            issues.extend(data)
            page += 1
            if len(data) < 100:
                break
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to retrieve data from GitHub: {e}")
            break
        except Exception as ex:
            st.error(f"An unexpected error occurred: {ex}")
            break
    return issues


# get_view_counts function removed

# --- Sidebar Filters ---
st.sidebar.header("Filters")

issue_state_filter: Literal["open", "closed", "all"] = st.sidebar.selectbox(
    "Issue State",
    options=["open", "closed", "all"],
    index=0,
    help="Select the state of issues to fetch.",
)

filter_closed_dates: Optional[Tuple[date, date]] = None
if issue_state_filter == "closed" or issue_state_filter == "all":
    dates_selected = st.sidebar.date_input(
        "Filter CLOSED issues by date range",
        value=None,
        max_value=date.today(),
        help="Select a start and end date. If only start is selected, end defaults to today.",
    )

    if dates_selected:
        if isinstance(dates_selected, tuple) and len(dates_selected) == 2:
            start_date_selected, end_date_selected = dates_selected
            if start_date_selected and end_date_selected:
                filter_closed_dates = (start_date_selected, end_date_selected)
            elif start_date_selected:
                filter_closed_dates = (start_date_selected, date.today())
        elif isinstance(dates_selected, date):
            filter_closed_dates = (dates_selected, date.today())

fetch_api_state: Literal["open", "closed", "all"]
if issue_state_filter == "all":
    fetch_api_state = "all"
elif issue_state_filter == "open":
    fetch_api_state = "open"
else:
    fetch_api_state = "closed"

with st.spinner(f"Fetching {fetch_api_state} issues..."):
    all_issues_raw = get_all_github_issues(state=fetch_api_state)

issues_without_prs = [issue for issue in all_issues_raw if "pull_request" not in issue]

all_labels_set = set()
for issue in issues_without_prs:
    for label in issue.get("labels", []):
        all_labels_set.add(label["name"])
sorted_labels = sorted(list(all_labels_set))

filter_by_labels = st.sidebar.multiselect(
    "Filter by labels (issues must have ALL selected labels)",
    options=sorted_labels,
    help="Select one or more labels. Issues must contain all selected labels to be included.",
)

# --- Filtering Logic ---
final_filtered_issues: List[Dict[str, Any]] = []
if not issues_without_prs:
    st.warning("No issues fetched from GitHub.")
else:
    for issue in issues_without_prs:
        if issue_state_filter != "all" and issue["state"] != issue_state_filter:
            continue

        if filter_by_labels:
            issue_label_names = [label["name"] for label in issue.get("labels", [])]
            if not all(
                selected_label in issue_label_names
                for selected_label in filter_by_labels
            ):
                continue

        if issue["state"] == "closed" and filter_closed_dates:
            start_date_filter, end_date_filter = filter_closed_dates
            try:
                closed_at_str = issue.get(
                    "closed_at"
                )  # Still need to fetch it for date filtering
                if closed_at_str:
                    closed_at_date = datetime.fromisoformat(
                        closed_at_str.replace("Z", "")
                    ).date()
                    if not (start_date_filter <= closed_at_date <= end_date_filter):
                        continue
                else:
                    continue  # If closed_at is missing for a supposedly closed issue, skip
            except ValueError:
                st.warning(
                    f"Could not parse close date for issue #{issue['number']}: {closed_at_str}"
                )
                continue

        final_filtered_issues.append(issue)

# --- Data Preparation and Export ---
if final_filtered_issues:
    st.success(f"{len(final_filtered_issues)} issues match your criteria.")

    # View count fetching logic removed

    export_data = []
    for i, issue in enumerate(final_filtered_issues):
        # View count related processing removed

        export_data.append(
            {
                "number": issue["number"],
                "title": issue["title"],
                "body": issue.get("body", ""),
                "state": issue["state"],
                "labels": [label["name"] for label in issue.get("labels", [])],
                "total_reactions_count": issue.get("reactions", {}).get(
                    "total_count", 0
                ),
                # comments, views, closed_at removed from export
                "created_at": issue["created_at"],
                "updated_at": issue["updated_at"],
                "url": issue["html_url"],
            }
        )

    if export_data:
        try:
            yaml_data = yaml.dump(export_data, allow_unicode=True, sort_keys=False)

            st.download_button(
                label="Download Issues as YAML",
                data=yaml_data,
                file_name="streamlit_issues.yaml",
                mime="text/yaml",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Error generating YAML file: {e}")
            st.error(
                "Please ensure the PyYAML library is installed and functioning correctly."
            )

    st.subheader(
        f"Preview of issues to be exported (first {min(5, len(export_data))} shown)"
    )
    for i, issue_data_preview in enumerate(export_data[:5]):
        st.markdown("---")
        st.markdown(
            f"**#{issue_data_preview['number']}: {issue_data_preview['title']}** (`{issue_data_preview['state']}`)"
        )
        with st.expander("Details"):
            preview_dict = {
                "body (first 200 chars)": (
                    issue_data_preview["body"][:200] + "..."
                    if issue_data_preview["body"]
                    and len(issue_data_preview["body"]) > 200
                    else issue_data_preview["body"]
                ),
                "labels": issue_data_preview["labels"],
                "total_reactions_count": issue_data_preview.get(
                    "total_reactions_count"
                ),
                # comments, views removed from preview
                "url": issue_data_preview["url"],
            }
            preview_dict_cleaned = {
                k: v for k, v in preview_dict.items() if v is not None
            }
            st.json(preview_dict_cleaned)

else:
    if issues_without_prs:
        st.warning("No issues found matching your filter criteria.")

st.sidebar.markdown("---")
st.sidebar.markdown("Developed with Streamlit.")
