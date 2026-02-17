import json
import operator
import urllib.request
from datetime import UTC, datetime

import pandas as pd
import streamlit as st

from app.utils.github_utils import get_all_github_issues

st.set_page_config(page_title="Bug prioritization", page_icon="🐛", layout="wide")

title_row = st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center")
with title_row:
    st.title("🐛 Bug prioritization")
    if st.button(":material/refresh: Refresh Data", type="tertiary"):
        get_all_github_issues.clear()

st.caption(
    "Explore the bugs and adapt prioritization based on the number of views, reactions, comments, and days since last updated."
)

# Mode selection
priority_mode = st.segmented_control(
    "Priority Action",
    options=[
        ":material/arrow_cool_down: Move Priority Down",
        ":material/arrow_warm_up: Move Priority Up",
    ],
    default=":material/arrow_cool_down: Move Priority Down",
    label_visibility="collapsed",
    width="stretch",
)

is_move_up = priority_mode == ":material/arrow_warm_up: Move Priority Up"

if is_move_up:
    st.caption("**Finding high-engagement issues** that may deserve higher priority (e.g., P3 → P2)")
else:
    st.caption("**Finding low-engagement issues** that may deserve lower priority (e.g., P3 → P4)")

# --- Helper Functions ---


@st.cache_data(ttl=60 * 60 * 12)  # cache for 12 hours
def get_view_counts(issue_numbers_series: pd.Series) -> pd.Series:
    # Get unique issue numbers and create batch request
    unique_issues = issue_numbers_series.unique()
    if len(unique_issues) == 0:
        return pd.Series(index=issue_numbers_series.index, dtype=float)

    # Process in batches of 100
    batch_size = 100
    view_counts = {}

    for i in range(0, len(unique_issues), batch_size):
        batch = unique_issues[i : i + batch_size]
        # Create batch request URL with current batch of issue numbers
        keys = ",".join(f"st-issue-{num}" for num in batch)
        url = f"https://api.views-badge.org/stats-batch?keys={keys}"

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request) as response:  # noqa: S310
                if not response or response.status != 200:
                    print("Failed to fetch issue view counts", flush=True)
                    continue

                data = json.loads(response.read().decode("utf-8"))

                # Add view counts from this batch to the mapping
                view_counts.update(
                    {int(key.split("-")[-1]): data.get(key, {}).get("views", None) or None for key in data}
                )
        except Exception:
            print("Failed to fetch issue view counts", flush=True)
            continue

    # Map the view counts back to the original series
    return issue_numbers_series.map(view_counts)


def labels_to_type(labels: list[str]) -> str:
    if "type:enhancement" in labels:
        return "✨"
    if "type:bug" in labels:
        return "🚨"
    if "type:docs" in labels:
        return "📚"
    if "type:kudos" in labels:
        return "🙏"
    return "❓"


REACTION_EMOJI = {
    "+1": "👍",
    "-1": "👎",
    "confused": "😕",
    "eyes": "👀",
    "heart": "❤️",
    "hooray": "🎉",
    "laugh": "😄",
    "rocket": "🚀",
}


def reactions_to_str(reactions: dict) -> str:
    return " ".join(
        [f"{reactions[name]} {emoji}" for name, emoji in REACTION_EMOJI.items() if reactions.get(name, 0) > 0]
    )


# --- Data Loading ---

with st.spinner("Fetching issues..."):
    # Fetch all open issues (we will filter for bugs later)
    all_issues = get_all_github_issues(state="open")

# Filter for type:bug
bug_issues = []
for issue in all_issues:
    if "pull_request" in issue:
        continue

    labels = [label["name"] for label in issue["labels"]]
    if "type:bug" in labels:
        bug_issues.append(issue)

if not bug_issues:
    st.warning("No bugs found!")
    st.stop()

df = pd.DataFrame(bug_issues)

# Pre-process labels for easier filtering
df["label_names"] = df["labels"].map(lambda x: [label["name"] for label in x])
df["total_reactions"] = df["reactions"].map(operator.itemgetter("total_count"))
df["reaction_types"] = df["reactions"].map(reactions_to_str)
df["author_avatar"] = df["user"].map(operator.itemgetter("avatar_url"))
df["assignee_avatar"] = df["assignee"].map(lambda x: x["avatar_url"] if x else None)

# Calculate days since updated
# Handle potential timezone differences (GitHub returns UTC ISO 8601)
# Using replace(tzinfo=None) for simple comparison or ensuring both are aware
now = datetime.now(UTC).replace(tzinfo=None)
df["updated_at_dt"] = pd.to_datetime(df["updated_at"]).dt.tz_localize(None)
df["days_since_updated"] = (now - df["updated_at_dt"]).dt.days

# --- Sidebar Filters ---

st.sidebar.header("Filters")

# 1. Priority Filter
# Extract all priority labels
all_priorities = set()
for labels in df["label_names"]:
    for label in labels:
        if label.startswith("priority:"):
            all_priorities.add(label)

sorted_priorities = sorted(all_priorities)
default_priorities = ["priority:P3"]
# Only use defaults that exist in the available priorities
default_priorities = [p for p in default_priorities if p in sorted_priorities]
selected_priorities = st.sidebar.multiselect(
    "Filter by Priority", options=sorted_priorities, default=default_priorities
)

# 2. Reactions Filter
if is_move_up:
    min_reactions = st.sidebar.number_input(
        "Min number of reactions",
        min_value=0,
        value=5,
        step=1,
        help="Show issues with at least this many reactions",
    )
else:
    max_reactions = st.sidebar.number_input("Max number of reactions", min_value=0, value=4, step=1)

# 3. Comments Filter
if is_move_up:
    min_comments = st.sidebar.number_input(
        "Min number of comments",
        min_value=0,
        value=3,
        step=1,
        help="Show issues with at least this many comments",
    )
else:
    max_comments = st.sidebar.number_input("Max number of comments", min_value=0, value=3, step=1)

# 4. Days Since Last Updated Filter
if is_move_up:
    max_days_since_update = st.sidebar.number_input(
        "Max days since last updated",
        min_value=0,
        value=30,
        step=1,
        help="Show issues updated within this many days (recently active)",
    )
else:
    min_days_since_update = st.sidebar.number_input(
        "Min days since last updated",
        min_value=0,
        value=90,
        step=1,
        help="Show issues updated at least this many days ago",
    )

# Apply Filters (except views, which we fetch after basic filtering to save API calls)
filtered_df = df.copy()

if selected_priorities:
    # Keep rows that have at least one of the selected priorities
    # Logic: Issue must have one of the selected priorities? Or ALL? usually ONE of.
    # If multiple selected, usually OR.
    def has_selected_priority(labels: list) -> bool:
        return any(p in labels for p in selected_priorities)

    filtered_df = filtered_df[filtered_df["label_names"].apply(has_selected_priority)]

# Apply reactions filter
if is_move_up:
    filtered_df = filtered_df[filtered_df["total_reactions"] >= min_reactions]
else:
    filtered_df = filtered_df[filtered_df["total_reactions"] <= max_reactions]

# Apply comments filter
if is_move_up:
    filtered_df = filtered_df[filtered_df["comments"] >= min_comments]
else:
    filtered_df = filtered_df[filtered_df["comments"] <= max_comments]

# Apply days since updated filter
if is_move_up:
    filtered_df = filtered_df[filtered_df["days_since_updated"] <= max_days_since_update]
else:
    filtered_df = filtered_df[filtered_df["days_since_updated"] >= min_days_since_update]

# 5. Max Views (Fetch views for filtered results)
# Fetch views only for the remaining issues to minimize API calls
if not filtered_df.empty:
    with st.spinner("Fetching view counts..."):
        filtered_df["views"] = get_view_counts(filtered_df["number"])
else:
    filtered_df["views"] = []

# 5. Views Filter
if is_move_up:
    min_views_input = st.sidebar.number_input(
        "Min number of views",
        min_value=0,
        value=100,
        step=1,
        help="Show issues with at least this many views",
    )
else:
    max_views_input = st.sidebar.number_input("Max number of views", min_value=0, value=100, step=1)

# Apply views filter
if not filtered_df.empty:
    if is_move_up:
        filtered_df = filtered_df[filtered_df["views"].fillna(0) >= min_views_input]
    else:
        filtered_df = filtered_df[filtered_df["views"].fillna(0) <= max_views_input]

# --- Display ---

st.markdown(f"Found **{len(filtered_df)}** bug issues matching criteria.")

if not filtered_df.empty:
    # Formatting for display
    filtered_df["type"] = filtered_df["label_names"].map(labels_to_type)
    filtered_df["title_display"] = filtered_df["type"] + filtered_df["title"]

    # Prepare final dataframe for display
    display_cols = [
        "title_display",
        "total_reactions",
        "views",
        "comments",
        "days_since_updated",
        "updated_at",
        "author_avatar",
        "html_url",
        "assignee_avatar",
        "state",
        "reaction_types",  # Optional
    ]

    # Configure columns
    column_config = {
        "title_display": st.column_config.TextColumn("Title", width="large"),
        "total_reactions": st.column_config.NumberColumn("Reactions", format="%d 🫶"),
        "views": st.column_config.NumberColumn("Views", format="%d 👁️"),
        "comments": st.column_config.NumberColumn("Comments", format="%d 💬"),
        "days_since_updated": st.column_config.NumberColumn("Days Since Update", format="%d days"),
        "updated_at": st.column_config.DatetimeColumn("Last Updated", format="distance"),
        "author_avatar": st.column_config.ImageColumn("Author"),
        "assignee_avatar": st.column_config.ImageColumn("Assignee"),
        "html_url": st.column_config.LinkColumn("Link", display_text="Open"),
        "state": "State",
        "reaction_types": "Reaction Types",
    }

    st.dataframe(
        filtered_df[display_cols],
        column_config=column_config,  # type: ignore[arg-type]
        hide_index=True,
        use_container_width=True,
    )
else:
    st.info("No issues match the current filters.")
