from __future__ import annotations

import pathlib
from typing import Literal

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

DEFAULT_ISSUES_FOLDER = "issues"
PATH_OF_SCRIPT = pathlib.Path(__file__).parent.resolve()
PATH_TO_ISSUES = (
    pathlib.Path(PATH_OF_SCRIPT).parent.joinpath(DEFAULT_ISSUES_FOLDER).resolve()
)

st.set_page_config(
    page_title="Issue Reactions Over Time",
    page_icon="🫶",
    initial_sidebar_state="collapsed",
)

st.title("🫶 Issue Reactions")


# Paginate through all open issues in the streamlit/streamlit repo
# and return them all as a list of dicts.
@st.cache_data(ttl=60 * 60 * 48)  # cache for 48 hours
def get_all_github_issues(state: Literal["open", "closed", "all"] = "all"):
    issues = []
    page = 1

    headers = {"Authorization": "token " + st.secrets["github"]["token"]}

    state_param = f"state={state}" if state else ""

    while True:
        try:
            response = requests.get(
                f"https://api.github.com/repos/streamlit/streamlit/issues?{state_param}&per_page=100&page={page}",
                headers=headers,
                timeout=100,
            )

            if response.status_code == 200:
                data = response.json()
                if not data:
                    break
                issues.extend(data)
                page += 1
            else:
                print(
                    f"Failed to retrieve data: {response.status_code}:", response.text
                )
                break
        except Exception as ex:
            print(ex, flush=True)
            break
    return issues


# Process the data
all_issues_df = pd.DataFrame(
    [issue for issue in get_all_github_issues() if "pull_request" not in issue]
)


all_issues_df["closed_at"] = pd.to_datetime(all_issues_df["closed_at"])
all_issues_df["total_reactions"] = all_issues_df["reactions"].apply(
    lambda x: x["total_count"]
)

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

    # Filter data based on selected date range
    start_date, end_date = date_range
    if start_date and end_date:
        df_filtered = all_issues_df[
            (all_issues_df["closed_at"].dt.date >= start_date)
            & (all_issues_df["closed_at"].dt.date <= end_date)
        ]
    else:
        df_filtered = all_issues_df

col1.markdown(
    f"##### Total Reactions on Closed Issues (Grouped by {time_grouping})",
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
st.plotly_chart(fig, use_container_width=True)

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

# Add a new section for feature labels chart

col1, col2 = st.columns([5, 1], vertical_alignment="bottom")

with col2.popover("Modify", use_container_width=True):
    top_x = st.slider("Show top", min_value=1, max_value=100, value=25)

col1.markdown(f"##### Top {top_x} Feature Labels by Reactions")

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
st.plotly_chart(fig_labels, use_container_width=True)
