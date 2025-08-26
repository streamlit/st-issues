from __future__ import annotations

import pathlib

import pandas as pd
import plotly.express as px
import streamlit as st

from app.utils.github_utils import get_all_github_issues

DEFAULT_ISSUES_FOLDER = "issues"
PATH_OF_SCRIPT = pathlib.Path(__file__).parent.resolve()
PATH_TO_ISSUES = (
    pathlib.Path(PATH_OF_SCRIPT).parent.joinpath(DEFAULT_ISSUES_FOLDER).resolve()
)

st.set_page_config(
    page_title="Issue Reactions",
    page_icon="👍",
)

st.title("🫶 Issue Reactions")
st.caption(
    "This page analyzes user reactions on Github issues (emoji reaction or comment)."
)


# Function to determine issue type based on labels
def get_issue_type(labels):
    is_bug = any(label["name"] == "type:bug" for label in labels)
    is_enhancement = any(label["name"] == "type:enhancement" for label in labels)

    if is_bug and is_enhancement:
        return ["Bug", "Enhancement"]
    elif is_bug:
        return "Bug"
    elif is_enhancement:
        return "Enhancement"
    else:
        return []


# Process the data
all_issues_df = pd.DataFrame(
    [issue for issue in get_all_github_issues() if "pull_request" not in issue]
)


all_issues_df["closed_at"] = pd.to_datetime(all_issues_df["closed_at"])
all_issues_df["total_reactions"] = all_issues_df["reactions"].apply(
    lambda x: x["total_count"]
)

with st.container(gap=None):
    col1, col2 = st.columns([5, 1], vertical_alignment="bottom")


    with col2.popover("Modify", use_container_width=True):
        # Allow user to select time grouping
        time_grouping = st.selectbox(
            "Group reactions by", options=["Day", "Week", "Month", "Year"], index=2
        )

        # Allow user to select date range
        date_range = st.date_input(
            "Select date range",
            value=(
                all_issues_df["closed_at"].min().date(),
                all_issues_df["closed_at"].max().date(),
            ),
            min_value=all_issues_df["closed_at"].min().date(),
            max_value=all_issues_df["closed_at"].max().date(),
        )

        # Filter who closed the issue:
        closed_by_filter = st.text_input(
            "Closed by", value=st.query_params.get("closed_by", "")
        )

        # Filter data based on selected date range
        start_date, end_date = date_range
        if start_date and end_date:
            df_filtered = all_issues_df[
                (all_issues_df["closed_at"].dt.date >= start_date)
                & (all_issues_df["closed_at"].dt.date <= end_date)
            ]
        else:
            df_filtered = all_issues_df

        if closed_by_filter:
            # Closed by contains a json string, we need to extract the name from it in the login
            df_filtered = df_filtered[
                df_filtered["closed_by"].apply(
                    lambda x: closed_by_filter.lower() in x.get("login", "").lower()
                    if x
                    else False
                )
            ]

    col1.markdown(
        f"##### Total Reactions on Closed Issues (Grouped by {time_grouping})",
    )
    st.caption(
        ":material/web_traffic: Click on a bar to view the issues closed in that time period."
    )

    # Group data based on selected time grouping
    if time_grouping == "Day":
        df_grouped = (
            df_filtered.groupby(df_filtered["closed_at"].dt.date)["total_reactions"]
            .sum()
            .reset_index()
        )
    elif time_grouping == "Week":
        df_grouped = (
            df_filtered.groupby(df_filtered["closed_at"].dt.to_period("W"))[
                "total_reactions"
            ]
            .sum()
            .reset_index()
        )
        df_grouped["closed_at"] = df_grouped["closed_at"].dt.start_time
    elif time_grouping == "Month":
        df_grouped = (
            df_filtered.groupby(df_filtered["closed_at"].dt.to_period("M"))[
                "total_reactions"
            ]
            .sum()
            .reset_index()
        )
        df_grouped["closed_at"] = df_grouped["closed_at"].dt.start_time
    else:  # Year
        df_grouped = (
            df_filtered.groupby(df_filtered["closed_at"].dt.year)["total_reactions"]
            .sum()
            .reset_index()
        )
        df_grouped["closed_at"] = pd.to_datetime(df_grouped["closed_at"], format="%Y")


    fig = px.bar(
        df_grouped,
        x="closed_at",
        y="total_reactions",
        labels={"closed_at": "Closed Date", "total_reactions": "Total Reactions"},
    )

    # Customize the chart
    fig.update_layout(
        xaxis_title="Closed Date",
        yaxis_title="Total Reactions",
        bargap=0.1,
    )


    # Display the chart
    event_data = st.plotly_chart(fig, use_container_width=True, on_select="rerun")

# Show issues for selected month when a bar is clicked
if event_data and "selection" in event_data and event_data["selection"]["points"]:
    selected_point = event_data["selection"]["points"][0]
    selected_date = pd.to_datetime(selected_point["x"])

    # Filter issues based on time grouping
    if time_grouping == "Day":
        selected_issues = df_filtered[
            df_filtered["closed_at"].dt.date == selected_date.date()
        ]
    elif time_grouping == "Week":
        # Convert to pandas Timestamp to handle timezone issues
        week_start = pd.Timestamp(selected_date)
        week_end = week_start + pd.Timedelta(days=6)

        # Convert datetime to date for comparison to avoid timezone issues
        selected_issues = df_filtered[
            (df_filtered["closed_at"].dt.date >= week_start.date())
            & (df_filtered["closed_at"].dt.date <= week_end.date())
        ]
    elif time_grouping == "Month":
        month_start = pd.to_datetime(selected_date)
        month_end = month_start + pd.offsets.MonthEnd(1)
        selected_issues = df_filtered[
            (df_filtered["closed_at"].dt.year == month_start.year)
            & (df_filtered["closed_at"].dt.month == month_start.month)
        ]
    else:  # Year
        selected_issues = df_filtered[
            df_filtered["closed_at"].dt.year == selected_date.year
        ]

    # Create a dataframe with the required columns
    if not selected_issues.empty:
        issues_df = pd.DataFrame(
            {
                "Title": selected_issues["title"],
                "Reactions": selected_issues["total_reactions"],
                "Type": selected_issues["labels"].apply(get_issue_type),
                "Closed on": selected_issues["closed_at"].dt.date,
                "Link": selected_issues["html_url"],
            }
        )

        # Sort by reactions in descending order
        issues_df = issues_df.sort_values("Reactions", ascending=False)

        # Create appropriate header based on time grouping
        if time_grouping == "Day":
            header_text = (
                f"##### Issues closed on {selected_date.strftime('%B %d, %Y')}"
            )
        elif time_grouping == "Week":
            week_end = pd.Timestamp(selected_date) + pd.Timedelta(days=6)
            header_text = f"##### Issues closed between {selected_date.strftime('%b %d')} and {week_end.strftime('%b %d, %Y')}"
        elif time_grouping == "Month":
            header_text = f"##### Issues closed in {selected_date.strftime('%B %Y')}"
        else:  # Year
            header_text = f"##### Issues closed in {selected_date.strftime('%Y')}"

        st.markdown(header_text)
        st.dataframe(
            issues_df,
            column_config={
                "Title": st.column_config.TextColumn(
                    width="large",
                ),
                "Link": st.column_config.LinkColumn(
                    display_text="issues/([0-9]+)",
                ),
                "Type": st.column_config.ListColumn(),
            },
            hide_index=True,
        )
    else:
        st.info(f"No issues found for the selected {time_grouping.lower()}.")

# Create the bar chart
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total issues", len(df_filtered))
with col2:
    st.metric("Total reactions", df_filtered["total_reactions"].sum())
with col3:
    st.metric(
        "Average reactions per issue",
        f"{df_filtered['total_reactions'].mean():.2f}",
    )

st.divider()


# Process data for feature labels
# Only use issues with state "open"
open_issues_df = all_issues_df[all_issues_df["state"] == "open"]
feature_labels = open_issues_df[
    open_issues_df["labels"].apply(
        lambda x: any(label["name"].startswith("feature:") for label in x)
    )
]
label_reactions = []

for _, issue in feature_labels.iterrows():
    for label in issue["labels"]:
        if label["name"].startswith("feature:"):
            label_reactions.append(
                {"label": label["name"], "reactions": issue["total_reactions"]}
            )

label_df = pd.DataFrame(label_reactions)

# Get the number of unique labels:
unique_labels = len(label_df["label"].unique())

col1, col2 = st.columns([5, 1], vertical_alignment="bottom")

with col2.popover("Modify", use_container_width=True):
    top_x = st.slider("Show top", min_value=1, max_value=unique_labels, value=15)

col1.markdown(f"##### Top {top_x} Feature Labels by Reactions")
st.caption(
    ":material/web_traffic: Click on a bar to view all open issues with that label."
)

top_labels = label_df.groupby("label")["reactions"].sum().nlargest(top_x).reset_index()
# Create the bar chart for top 10 feature labels
fig_labels = px.bar(
    top_labels,
    x="label",
    y="reactions",
    labels={"label": "Feature Label", "reactions": "Total Reactions"},
)

# Customize the chart
fig_labels.update_layout(
    xaxis_title="Feature Label",
    yaxis_title="Total Reactions",
    xaxis_tickangle=-45,
    bargap=0.1,
)

# Display the chart
feature_event_data = st.plotly_chart(
    fig_labels, use_container_width=True, on_select="rerun"
)

# Show issues for selected feature label when a bar is clicked
if (
    feature_event_data
    and "selection" in feature_event_data
    and feature_event_data["selection"]["points"]
):
    selected_point = feature_event_data["selection"]["points"][0]
    selected_label = selected_point["x"]

    # Filter issues with the selected feature label
    selected_feature_issues = open_issues_df[
        open_issues_df["labels"].apply(
            lambda x: any(label["name"] == selected_label for label in x)
        )
    ]

    # Create a dataframe with the required columns
    if not selected_feature_issues.empty:
        feature_issues_df = pd.DataFrame(
            {
                "Title": selected_feature_issues["title"],
                "Reactions": selected_feature_issues["total_reactions"],
                "Type": selected_feature_issues["labels"].apply(get_issue_type),
                "Created on": pd.to_datetime(
                    selected_feature_issues["created_at"]
                ).dt.date,
                "Link": selected_feature_issues["html_url"],
            }
        )

        # Sort by reactions in descending order
        feature_issues_df = feature_issues_df.sort_values("Reactions", ascending=False)

        st.markdown(f"##### Issues with label: {selected_label}")
        st.dataframe(
            feature_issues_df,
            column_config={
                "Title": st.column_config.TextColumn(
                    width="large",
                ),
                "Link": st.column_config.LinkColumn(
                    display_text="issues/([0-9]+)",
                ),
                "Type": st.column_config.ListColumn(),
            },
            hide_index=True,
        )
    else:
        st.info("No issues found with the selected feature label.")
