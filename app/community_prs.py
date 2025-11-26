from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from app.utils.github_utils import (
    STREAMLIT_TEAM_MEMBERS,
    fetch_pr_info,
    get_all_github_prs,
)

st.set_page_config(
    page_title="Community PRs",
    page_icon="👥",
)

title_row = st.container(
    horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"
)
with title_row:
    st.title("👥 Community PRs")
    if st.button(":material/refresh: Refresh Data", type="tertiary"):
        get_all_github_prs.clear()

st.caption(
    "Explore contributions from the Streamlit community through pull requests on the streamlit/streamlit repo."
)


# Process the data
all_prs_df = pd.DataFrame(get_all_github_prs("all"))

# Convert date strings to datetime objects
all_prs_df["created_at"] = pd.to_datetime(all_prs_df["created_at"])
all_prs_df["closed_at"] = pd.to_datetime(all_prs_df["closed_at"])
all_prs_df["merged_at"] = pd.to_datetime(all_prs_df["merged_at"])

# Extract author information
all_prs_df["author"] = all_prs_df["user"].apply(lambda x: x["login"] if x else "")


# Function to extract change types from labels
def get_change_types(labels):
    change_types = []
    for label in labels:
        label_name = label["name"]
        if label_name.startswith("change:"):
            # Extract the type after "change:" and capitalize the first letter
            change_type = label_name.replace("change:", "").capitalize()
            change_types.append(change_type)
    return change_types


# Extract change types from labels
all_prs_df["change_types"] = all_prs_df["labels"].apply(get_change_types)

# Add a status column to distinguish between merged, closed without merge, and open PRs
all_prs_df["status"] = "Open"
all_prs_df.loc[all_prs_df["merged_at"].notna(), "status"] = "Merged"
all_prs_df.loc[
    (all_prs_df["closed_at"].notna()) & (all_prs_df["merged_at"].isna()), "status"
] = "Closed without merge"

# Count PRs by author and sort authors by PR count
author_counts = all_prs_df["author"].value_counts().to_dict()
unique_authors = sorted(
    all_prs_df["author"].unique(), key=lambda x: (-author_counts[x], x)
)
sfc_authors = [author for author in unique_authors if author.startswith("sfc-gh-")]
bot_authors = [
    author
    for author in unique_authors
    if author.endswith("[bot]") or author.endswith("bot")
]
deleted_authors = [author for author in unique_authors if author == "ghost"]
other_authors = [
    author
    for author in unique_authors
    if not author.startswith("sfc-gh-")
    and not (author.endswith("[bot]") or author.endswith("bot"))
    and author != "ghost"
]

# Author filtering in an expander
with st.expander("Filter authors", expanded=False):
    # Checkboxes for common exclusions
    col1, col2, col3 = st.columns(3)

    with col1:
        exclude_sfc = st.checkbox("Exclude sfc-gh-* authors", value=True)

    with col2:
        exclude_bots = st.checkbox("Exclude bot authors", value=True)

    with col3:
        exclude_deleted = st.checkbox("Exclude deleted authors", value=True)

    # Determine which authors are available and excluded by default
    excluded_authors = []

    if exclude_sfc:
        excluded_authors.extend(sfc_authors)
        available_authors = other_authors
    else:
        available_authors = unique_authors

    if exclude_bots:
        excluded_authors.extend(bot_authors)
        available_authors = [
            author
            for author in available_authors
            if not (author.endswith("[bot]") or author.endswith("bot"))
        ]

    if exclude_deleted:
        excluded_authors.extend(deleted_authors)
        available_authors = [
            author for author in available_authors if author != "ghost"
        ]

    # Add PR count to author names for display
    author_options = [
        f"{author} ({author_counts[author]} PRs)" for author in available_authors
    ]

    # Find default selections - authors from STREAMLIT_AUTHORS that are in available_authors
    default_selections = [
        f"{author} ({author_counts[author]} PRs)"
        for author in available_authors
        if author in STREAMLIT_TEAM_MEMBERS
    ]

    # Multiselect for additional exclusions
    excluded_author_indices = st.multiselect(
        "Exclude additional authors (mostly employees' private GitHub accounts)",
        options=author_options,
        default=default_selections,
    )

    # Extract author names from the selected options
    additional_excluded_authors = [
        available_authors[author_options.index(option)]
        for option in excluded_author_indices
    ]
    excluded_authors.extend(additional_excluded_authors)

# Filter out excluded authors
if excluded_authors:
    all_prs_df = all_prs_df[~all_prs_df["author"].isin(excluded_authors)]

# Get all unique change types across all PRs
all_change_types = set()
for types_list in all_prs_df["change_types"]:
    all_change_types.update(types_list)
all_change_types = sorted(list(all_change_types))


# Filter by PR type
if all_change_types:
    # Set default to all change types
    selected_change_types = st.multiselect(
        "Filter by PR type",
        options=all_change_types,
        default=all_change_types,
    )

    include_no_type = st.checkbox(
        "Include PRs without type",
        value=False,
        help="Note that we introduced PR type labels in mid-2023, so issues before then "
        "will only be included if you check this checkbox.",
    )

# Filter PRs to include those with selected change types and optionally those without types
if selected_change_types or include_no_type:
    all_prs_df = all_prs_df[
        all_prs_df["change_types"].apply(
            lambda types: (
                any(t in selected_change_types for t in types)
                if types
                else include_no_type
            )
        )
    ]

# Filter by PR status
status_filter = st.multiselect(
    "Filter by PR status",
    options=["Open", "Merged", "Closed without merge"],
    default=["Open", "Merged", "Closed without merge"],
)

st.write("")
st.write("")

# Apply status filter to the dataframe
if status_filter:
    all_prs_df = all_prs_df[all_prs_df["status"].isin(status_filter)]

col1, col2 = st.columns([5, 1], vertical_alignment="bottom")

with col2.popover("Modify", width="stretch"):
    # Allow user to select time grouping
    time_grouping = st.selectbox(
        "Group PRs by", options=["Day", "Week", "Month", "Year"], index=2
    )

    # Allow user to select date range
    min_possible_date = all_prs_df["created_at"].min().date()
    max_date = datetime.now().date()

    # Default to starting from 2021-01-01
    default_start_date = datetime(2021, 1, 1).date()
    if min_possible_date > default_start_date:
        default_start_date = min_possible_date

    date_range = st.date_input(
        "Select date range",
        value=(default_start_date, max_date),
        min_value=min_possible_date,
        max_value=max_date,
    )

    # Filter data based on selected date range
    start_date, end_date = date_range
    if start_date and end_date:
        df_filtered = all_prs_df[
            (all_prs_df["created_at"].dt.date >= start_date)
            & (all_prs_df["created_at"].dt.date <= end_date)
        ]
    else:
        df_filtered = all_prs_df

col1.markdown(
    f"##### PRs over time (grouped by {time_grouping.lower()})",
)
st.caption(
    ":material/web_traffic: Click on a bar to view the community PRs opened in that time period."
)

# Group data based on selected time grouping
if time_grouping == "Day":
    df_grouped = (
        df_filtered.groupby([df_filtered["created_at"].dt.date, "status"])
        .size()
        .reset_index(name="count")
    )
elif time_grouping == "Week":
    df_filtered["week"] = df_filtered["created_at"].dt.to_period("W")
    df_grouped = (
        df_filtered.groupby([df_filtered["week"], "status"])
        .size()
        .reset_index(name="count")
    )
    df_grouped["created_at"] = df_grouped["week"].dt.start_time
    df_grouped = df_grouped.drop("week", axis=1)
elif time_grouping == "Month":
    df_filtered["month"] = df_filtered["created_at"].dt.to_period("M")
    df_grouped = (
        df_filtered.groupby([df_filtered["month"], "status"])
        .size()
        .reset_index(name="count")
    )
    df_grouped["created_at"] = df_grouped["month"].dt.start_time
    df_grouped = df_grouped.drop("month", axis=1)
else:  # Year
    df_filtered["year"] = df_filtered["created_at"].dt.year
    df_grouped = (
        df_filtered.groupby([df_filtered["year"], "status"])
        .size()
        .reset_index(name="count")
    )
    df_grouped["created_at"] = pd.to_datetime(df_grouped["year"], format="%Y")
    df_grouped = df_grouped.drop("year", axis=1)

# Create the stacked bar chart
fig = px.bar(
    df_grouped,
    x="created_at",
    y="count",
    color="status",
    labels={
        "created_at": "Created date",
        "count": "Number of PRs",
        "status": "PR status",
    },
    color_discrete_map={
        "Open": "#FFA500",  # Orange
        "Merged": "#008000",  # Green
        "Closed without merge": "#FF0000",  # Red
    },
)

# Customize the chart
fig.update_layout(
    xaxis_title="Created date",
    yaxis_title="Number of PRs",
    bargap=0.1,
    legend_title="PR status",
)

# Display the chart
event_data = st.plotly_chart(fig, width="stretch", on_select="rerun")

# Show PRs for selected time period when a bar is clicked
if event_data and "selection" in event_data and event_data["selection"]["points"]:
    selected_point = event_data["selection"]["points"][0]
    selected_date = pd.to_datetime(selected_point["x"])
    selected_status = (
        selected_point.get("customdata", [None])[0]
        if "customdata" in selected_point
        else None
    )

    # Filter PRs based on time grouping
    if time_grouping == "Day":
        selected_prs = df_filtered[
            df_filtered["created_at"].dt.date == selected_date.date()
        ]
    elif time_grouping == "Week":
        # Convert to pandas Timestamp to handle timezone issues
        week_start = pd.Timestamp(selected_date)
        week_end = week_start + pd.Timedelta(days=6)

        # Convert datetime to date for comparison to avoid timezone issues
        selected_prs = df_filtered[
            (df_filtered["created_at"].dt.date >= week_start.date())
            & (df_filtered["created_at"].dt.date <= week_end.date())
        ]
    elif time_grouping == "Month":
        month_start = pd.to_datetime(selected_date)
        month_end = month_start + pd.offsets.MonthEnd(1)
        selected_prs = df_filtered[
            (df_filtered["created_at"].dt.year == month_start.year)
            & (df_filtered["created_at"].dt.month == month_start.month)
        ]
    else:  # Year
        selected_prs = df_filtered[
            df_filtered["created_at"].dt.year == selected_date.year
        ]

    # Filter by status if a specific status bar was clicked
    if selected_status:
        selected_prs = selected_prs[selected_prs["status"] == selected_status]

    # Create a dataframe with the required columns
    if not selected_prs.empty:
        prs_df = pd.DataFrame(
            {
                "Title": selected_prs["title"],
                "Status": selected_prs["status"],
                "Created on": selected_prs["created_at"].dt.date,
                "Author": selected_prs["author"].apply(
                    lambda x: f"https://github.com/{x}"
                ),
                "Change types": selected_prs["change_types"],
                "Link": selected_prs["html_url"],
            }
        )

        # Sort by created date in descending order
        prs_df = prs_df.sort_values("Created on", ascending=False)

        # Create appropriate header based on time grouping
        if time_grouping == "Day":
            header_text = f"##### PRs opened on {selected_date.strftime('%B %d, %Y')}"
        elif time_grouping == "Week":
            week_end = pd.Timestamp(selected_date) + pd.Timedelta(days=6)
            header_text = f"##### PRs opened between {selected_date.strftime('%b %d')} and {week_end.strftime('%b %d, %Y')}"
        elif time_grouping == "Month":
            header_text = f"##### PRs opened in {selected_date.strftime('%B %Y')}"
        else:  # Year
            header_text = f"##### PRs opened in {selected_date.strftime('%Y')}"

        if selected_status:
            header_text += f" ({selected_status})"

        st.markdown(header_text)
        st.dataframe(
            prs_df,
            column_config={
                "Title": st.column_config.TextColumn(
                    width="large",
                ),
                "Link": st.column_config.LinkColumn(
                    display_text="pull/([0-9]+)",
                ),
                "Author": st.column_config.LinkColumn(
                    display_text="github.com/([^/]+)",
                    help="GitHub username",
                ),
                "Change types": st.column_config.ListColumn(
                    width="medium",
                ),
            },
            hide_index=True,
        )
    else:
        st.info(f"No PRs found for the selected {time_grouping.lower()}.")

# Create metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total PRs", len(df_filtered))
with col2:
    st.metric("Open PRs", len(df_filtered[df_filtered["status"] == "Open"]))
with col3:
    st.metric("Merged PRs", len(df_filtered[df_filtered["status"] == "Merged"]))
with col4:
    st.metric(
        "Closed without merge",
        len(df_filtered[df_filtered["status"] == "Closed without merge"]),
    )

st.divider()

# PR Velocity Analysis
st.markdown("##### PR review velocity")
st.caption("This shows how quickly community contributions are reviewed and processed.")

# Calculate time to merge/close for each PR
df_filtered["days_to_merge"] = (
    df_filtered["merged_at"] - df_filtered["created_at"]
).dt.days
df_filtered["days_to_close"] = (
    df_filtered["closed_at"] - df_filtered["created_at"]
).dt.days

# Filter out PRs that are still open
closed_prs = df_filtered[df_filtered["closed_at"].notna()]

# Group by month and calculate average time to merge/close
if not closed_prs.empty:
    closed_prs["month"] = closed_prs["closed_at"].dt.to_period("M")

    # Calculate average time to merge/close by month
    velocity_df = (
        closed_prs.groupby("month")
        .agg(
            {
                "days_to_merge": "mean",
                "days_to_close": "mean",
            }
        )
        .reset_index()
    )

    velocity_df["month"] = velocity_df["month"].dt.start_time

    # Create a line chart for PR velocity
    fig_velocity = px.line(
        velocity_df,
        x="month",
        y=["days_to_merge", "days_to_close"],
        labels={"month": "Month", "value": "Average days", "variable": "Metric"},
        title="Average time to merge/close PRs by month",
    )

    # Customize the chart
    fig_velocity.update_layout(
        xaxis_title="Month",
        yaxis_title="Average days",
        legend_title="Metric",
    )

    # Display the chart
    st.plotly_chart(fig_velocity, width="stretch")

    # Display overall metrics
    col1, col2 = st.columns(2)

    with col1:
        avg_merge_time = closed_prs[closed_prs["merged_at"].notna()][
            "days_to_merge"
        ].mean()
        st.metric("Average days to merge", f"{avg_merge_time:.1f} days")

    with col2:
        avg_close_time = closed_prs["days_to_close"].mean()
        st.metric("Average days to close", f"{avg_close_time:.1f} days")
else:
    st.info("No closed PRs in the selected date range.")

# Top Contributors Analysis
st.divider()
st.markdown("##### Top contributors")
st.caption(
    "These are the most active community contributors based on their pull requests."
)

# Get PR counts by author
author_pr_counts = df_filtered["author"].value_counts().reset_index()
author_pr_counts.columns = ["Author", "Number of PRs"]

# Get merged PR counts by author
merged_prs = df_filtered[df_filtered["status"] == "Merged"]
author_merged_counts = merged_prs["author"].value_counts().to_dict()

# Calculate merge rate for each author
author_pr_counts["Merged PRs"] = author_pr_counts["Author"].apply(
    lambda x: author_merged_counts.get(x, 0)
)
# Calculate merge rate as percentage (0-100) instead of decimal (0-1)
author_pr_counts["Merge rate"] = (
    author_pr_counts["Merged PRs"] / author_pr_counts["Number of PRs"] * 100
)

# Calculate average time to merge for each author
author_merge_times = {}
for author in author_pr_counts["Author"]:
    author_merged = merged_prs[merged_prs["author"] == author]
    if not author_merged.empty:
        author_merge_times[author] = author_merged["days_to_merge"].mean()
    else:
        author_merge_times[author] = None

author_pr_counts["Avg days to merge"] = author_pr_counts["Author"].apply(
    lambda x: author_merge_times.get(x)
)

# Get change types distribution for each author
author_change_types = {}
for author in author_pr_counts["Author"].str.replace("https://github.com/", ""):
    author_prs = df_filtered[df_filtered["author"] == author]
    if not author_prs.empty:
        # Flatten the list of change types for this author
        all_types = [t for types_list in author_prs["change_types"] for t in types_list]
        if all_types:
            # Get the most common change type
            from collections import Counter

            most_common = Counter(all_types).most_common(1)
            author_change_types[author] = most_common[0][0] if most_common else None
        else:
            author_change_types[author] = None
    else:
        author_change_types[author] = None

# Add most common change type for each author
author_pr_counts["Most common change"] = author_pr_counts["Author"].apply(
    lambda x: author_change_types.get(x.replace("https://github.com/", ""))
)

# Add GitHub profile URL for display
author_pr_counts["Author"] = author_pr_counts["Author"].apply(
    lambda x: f"https://github.com/{x}"
)

# Show top 20 contributors by default
top_contributors = author_pr_counts.head(20)

# Display the dataframe
st.dataframe(
    top_contributors,
    column_config={
        "Author": st.column_config.LinkColumn(
            display_text="github.com/([^/]+)",
        ),
        "Number of PRs": st.column_config.NumberColumn(
            format="%d",
        ),
        "Merged PRs": st.column_config.NumberColumn(
            format="%d",
        ),
        "Merge rate": st.column_config.ProgressColumn(
            format="%d%%",
            min_value=0,
            max_value=100,  # Changed max_value to 100 since we're using percentages now
        ),
        "Avg days to merge": st.column_config.NumberColumn(
            format="%.1f days",
        ),
        "Most common change": st.column_config.ListColumn(),
    },
    hide_index=True,
)

st.divider()

# Top Mergers Analysis
st.markdown("##### Top mergers")
st.caption(
    "Maintainers who merged the most community PRs based on the current filters."
)


# Helper to fetch the user who merged a PR (cached)
@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_merged_by_login(pr_number: int) -> str | None:
    pr_info = fetch_pr_info(str(pr_number))
    if not pr_info:
        return None
    merged_by = pr_info.get("merged_by")
    if merged_by and isinstance(merged_by, dict):
        return merged_by.get("login")
    return None


merged_prs_only = df_filtered[df_filtered["status"] == "Merged"].copy()

if merged_prs_only.empty:
    st.info("No merged PRs in the selected filters.")
else:
    with st.spinner("Fetching merger info for merged PRs..."):
        merged_prs_only["merged_by_login"] = merged_prs_only["number"].apply(
            get_merged_by_login
        )

    # Drop PRs where merger info is unavailable
    merged_prs_only = merged_prs_only.dropna(subset=["merged_by_login"])

    if merged_prs_only.empty:
        st.info("No merger information available for the selected PRs.")
    else:
        # Aggregate counts and average time-to-merge per merger
        merger_counts = (
            merged_prs_only.groupby("merged_by_login")
            .size()
            .reset_index(name="Merged PRs")
        )

        top_mergers_df = merger_counts.rename(columns={"merged_by_login": "Merger"})

        # Add GitHub profile URL for display
        top_mergers_df["Merger"] = top_mergers_df["Merger"].apply(
            lambda x: f"https://github.com/{x}"
        )

        # Sort and limit
        top_mergers_df = top_mergers_df.sort_values("Merged PRs", ascending=False).head(
            50
        )

        st.dataframe(
            top_mergers_df,
            column_config={
                "Merger": st.column_config.LinkColumn(
                    display_text="github.com/([^/]+)",
                ),
                "Merged PRs": st.column_config.NumberColumn(
                    format="%d",
                ),
            },
            hide_index=True,
        )
