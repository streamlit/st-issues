from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Replace Visit Badges", page_icon="🔄")

st.title("🔄 Replace Visit Badges")

st.markdown("""
This app allows you to replace old visit badges with new ones in GitHub issue comments.

**Old Badge Formats:**
```
![Visits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Fstreamlit%2Fstreamlit%2Fissues%2F${{ github.event.issue.number }}&title=visits&edge_flat=false)
```

```
![Views](https://api.visitorbadge.io/api/combined?path=https%3A%2F%2Fgithub.com%2Fstreamlit%2Fstreamlit%2Fissues%2F${{ github.event.issue.number }}&label=Views&style=flat-square&labelStyle=none)
```

**New Badge:**
```
![Views](https://api.views-badge.org/badge/st-issue-${{ github.event.issue.number }})
```
""")

# Allow user to specify the number of issues to update
max_issues_to_update = st.number_input(
    "Maximum number of issues to update",
    min_value=1,
    max_value=1000,
    value=50,
    help="Limit the number of issues to update to avoid hitting API rate limits",
)

# Add maximum issue number filter
max_issue_number = st.number_input(
    "Maximum issue number to process",
    min_value=1,
    value=None,
    max_value=20000,
    help="Only process issues with numbers less than or equal to this value",
)

# Option to filter issues by labels
with st.expander("Filter issues"):
    filter_by_label = st.checkbox("Filter by labels", value=True)

    label_options = []
    if filter_by_label:
        label_options = st.multiselect(
            "Select labels",
            ["type:enhancement", "type:bug"],
            default=["type:enhancement"],
            help="Only process issues with these labels",
        )

# Status placeholder
status = st.empty()

# Results container
results_container = st.container()


@st.cache_data(ttl=60 * 60)  # cache for 1 hour
def get_github_issues(
    state: str = "open",
    labels: Optional[List[str]] = None,
    max_issues: int = 100,
    max_issue_number: int | None = None,
):
    """Get issues from the GitHub API"""
    issues = []
    page = 1
    total_issues = 0

    headers = {"Authorization": "token " + st.secrets["github"]["token"]}

    label_param = ""
    if labels and len(labels) > 0:
        label_param = "&labels=" + ",".join(labels)

    while total_issues < max_issues:
        try:
            url = f"https://api.github.com/repos/streamlit/streamlit/issues?state={state}&per_page=100&page={page}{label_param}"
            response = requests.get(
                url,
                headers=headers,
                timeout=100,
            )

            if response.status_code == 200:
                data = response.json()
                if not data:
                    break

                # Filter out pull requests and issues with numbers higher than max_issue_number
                issues_only = [
                    issue
                    for issue in data
                    if "pull_request" not in issue
                    and (
                        max_issue_number is None or issue["number"] <= max_issue_number
                    )
                ]

                # Add only what we need to reach max_issues
                remaining_slots = max_issues - total_issues
                issues.extend(issues_only[:remaining_slots])

                total_issues = len(issues)

                # If we got less than 100 issues or we've reached our limit, we're done
                if len(data) < 100 or total_issues >= max_issues:
                    break

                page += 1
            else:
                st.error(
                    f"Failed to retrieve issues: {response.status_code}\n{response.text}"
                )
                break
        except Exception as ex:
            st.error(f"Error fetching issues: {ex}")
            break

    return issues


def get_issue_comments(issue_number: int) -> List[Dict[str, Any]]:
    """Get comments for a specific issue"""
    headers = {"Authorization": "token " + st.secrets["github"]["token"]}

    try:
        response = requests.get(
            f"https://api.github.com/repos/streamlit/streamlit/issues/{issue_number}/comments",
            headers=headers,
            timeout=100,
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(
                f"Failed to retrieve comments for issue #{issue_number}: {response.status_code}"
            )
    except Exception as ex:
        st.error(f"Error fetching comments for issue #{issue_number}: {ex}")

    return []


def update_comment(comment_id: int, new_body: str) -> bool:
    """Update a comment with new content"""
    headers = {"Authorization": "token " + st.secrets["github"]["token"]}

    try:
        response = requests.patch(
            f"https://api.github.com/repos/streamlit/streamlit/issues/comments/{comment_id}",
            headers=headers,
            json={"body": new_body},
            timeout=100,
        )

        if response.status_code == 200:
            return True
        else:
            st.error(
                f"Failed to update comment {comment_id}: {response.status_code}\n{response.text}"
            )
    except Exception as ex:
        st.error(f"Error updating comment {comment_id}: {ex}")

    return False


def replace_badge(comment_body: str, issue_number: int) -> Optional[str]:
    """Replace the old visit badges with the new one"""
    # Old badge patterns
    old_seeyoufarm_pattern = r"!\[Visits\]\(https://hits\.seeyoufarm\.com/api/count/(?:incr/)?badge\.svg\?url=https%3A%2F%2Fgithub\.com%2Fstreamlit%2Fstreamlit%2Fissues%2F\d+(?:&title=visits)?(?:&edge_flat=false)?\)"
    old_visitorbadge_pattern = r"!\[Views\]\(https://api\.visitorbadge\.io/api/combined\?path=https%3A%2F%2Fgithub\.com%2Fstreamlit%2Fstreamlit%2Fissues%2F\d+&label=Views&style=flat-square&labelStyle=none\)"

    # New badge format with the actual issue number
    new_badge = f"![Views](https://api.views-badge.org/badge/st-issue-{issue_number})"

    # Check if comment contains any of the old badges
    if re.search(old_seeyoufarm_pattern, comment_body):
        return re.sub(old_seeyoufarm_pattern, new_badge, comment_body)
    elif re.search(old_visitorbadge_pattern, comment_body):
        return re.sub(old_visitorbadge_pattern, new_badge, comment_body)

    return None


def process_issues():
    selected_labels = label_options if filter_by_label else None

    with status.status("Fetching issues..."):
        issues = get_github_issues(
            state="open",
            labels=selected_labels,
            max_issues=max_issues_to_update,
            max_issue_number=max_issue_number,
        )

        if not issues:
            st.warning("No issues found with the specified criteria.")
            return

        st.write(f"Found {len(issues)} issues to process.")

        results = {
            "issue_number": [],
            "issue_title": [],
            "comment_updated": [],
            "error": [],
            "link": [],
        }

        progress_bar = st.progress(0)

        for i, issue in enumerate(issues):
            issue_number = issue["number"]
            issue_title = issue["title"]

            st.write(f"Processing issue #{issue_number}: {issue_title}")

            # Get comments for the issue
            comments = get_issue_comments(issue_number)

            updated = False
            error = ""

            for comment in comments:
                # Check if this is likely a community voting comment
                if (
                    "prioritize this feature" in comment["body"]
                    or "If this issue affects you" in comment["body"]
                ):
                    # Try to replace the badge
                    new_body = replace_badge(comment["body"], issue_number)

                    if new_body:
                        # Update the comment
                        success = update_comment(comment["id"], new_body)

                        if success:
                            updated = True
                            break
                        else:
                            error = "Failed to update comment"
                    else:
                        # If comment matches voting pattern but no badge found
                        if "views-badge.org" in comment["body"]:
                            updated = True  # Already has new badge
                            break
                        error = "No old badge found"

            results["issue_number"].append(issue_number)
            results["issue_title"].append(issue_title)
            results["comment_updated"].append(updated)
            results["error"].append(error)
            results["link"].append(
                f"https://github.com/streamlit/streamlit/issues/{issue_number}"
            )

            # Update progress
            progress_bar.progress((i + 1) / len(issues))

            # Add a small delay to avoid hitting rate limits
            time.sleep(0.5)

        return pd.DataFrame(results)


# Start button
if st.button("Start Badge Replacement", type="primary"):
    df = process_issues()

    if df is not None:
        with results_container:
            st.subheader("Results")

            # Count of successful updates
            successful_updates = df["comment_updated"].sum()
            total_issues = len(df)

            st.metric(
                "Badges Updated",
                f"{successful_updates}/{total_issues}",
                help="Number of issues where badges were successfully updated",
            )

            # Display detailed results
            st.dataframe(
                df,
                column_config={
                    "issue_number": st.column_config.NumberColumn(
                        "Issue #", help="GitHub issue number", format="%d"
                    ),
                    "issue_title": "Title",
                    "comment_updated": st.column_config.CheckboxColumn(
                        "Updated", help="Whether the badge was successfully updated"
                    ),
                    "error": "Error (if any)",
                    "link": st.column_config.LinkColumn(
                        "Link",
                        help="Click to view issue on GitHub",
                        display_text="View on GitHub",
                        width="small",
                    ),
                },
            )

            # Link issues with errors for manual review
            failed_issues = df[~df["comment_updated"]]
            if not failed_issues.empty:
                st.subheader("Issues requiring manual review")
                for _, row in failed_issues.iterrows():
                    issue_num = row["issue_number"]
                    st.markdown(
                        f"[Issue #{issue_num}: {row['issue_title']}](https://github.com/streamlit/streamlit/issues/{issue_num}) - Error: {row['error']}"
                    )
