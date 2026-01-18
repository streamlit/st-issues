from __future__ import annotations

from datetime import datetime, timedelta

import humanize
import pandas as pd
import plotly.express as px
import streamlit as st

from app.utils.github_utils import fetch_artifacts, fetch_workflow_runs

st.set_page_config(page_title="Wheel Size", page_icon="🛞")

title_row = st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center")
with title_row:
    st.title("🛞 Wheel Size")
    if st.button(":material/refresh: Refresh Data", type="tertiary"):
        fetch_workflow_runs.clear()
st.caption("This page visualizes the size of wheel files created in the PR preview workflow.")

# Sidebar controls
time_period = st.sidebar.selectbox(
    "Time period",
    options=["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
    help="The time period to display the wheel size for. But it will still only load the last X workflow runs as defined by the slider below.",
    index=3,
)
workflow_runs_limit = st.sidebar.slider(
    "Number of workflow runs",
    min_value=100,
    max_value=500,
    value=100,
    step=100,
    help="This is equivalent to the number of commits to develop to include in the analysis.",
)


# Convert time period to date
since_date: datetime | None
if time_period == "Last 7 days":
    since_date = datetime.now() - timedelta(days=7)
elif time_period == "Last 30 days":
    since_date = datetime.now() - timedelta(days=30)
elif time_period == "Last 90 days":
    since_date = datetime.now() - timedelta(days=90)
else:
    since_date = None


# Fetch workflow runs
with st.spinner("Fetching data..."):
    workflow_runs = fetch_workflow_runs("pr-preview.yml", limit=workflow_runs_limit, since=since_date)

    if not workflow_runs:
        st.warning("No workflow runs found for the specified criteria.")
        st.stop()

    # Process the data
    wheel_sizes = []

    for run in workflow_runs:
        artifacts = fetch_artifacts(run["id"])

        for artifact in artifacts:
            if artifact["name"] == "whl_file":
                wheel_sizes.append(
                    {
                        "run_id": run["id"],
                        "commit_sha": run["head_sha"][:7],
                        "commit_url": f"https://github.com/streamlit/streamlit/commit/{run['head_sha']}",
                        "created_at": datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                        "size_bytes": artifact["size_in_bytes"],
                        "size_mb": artifact["size_in_bytes"] / (1024 * 1024),
                        "size_human": humanize.naturalsize(artifact["size_in_bytes"], binary=True),
                        "artifact_url": artifact["archive_download_url"],
                        "run_url": run["html_url"],
                    }
                )
                break

    # Create DataFrame
    if wheel_sizes:
        df = pd.DataFrame(wheel_sizes)
        df = df.sort_values("created_at")
    else:
        st.warning("No wheel artifacts found in the workflow runs.")
        st.stop()

# Display metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Average Size", humanize.naturalsize(df["size_bytes"].mean(), binary=True))
with col2:
    st.metric("Minimum Size", humanize.naturalsize(df["size_bytes"].min(), binary=True))
with col3:
    st.metric("Maximum Size", humanize.naturalsize(df["size_bytes"].max(), binary=True))

# Create time series chart
st.subheader("Wheel Size Over Time")

fig = px.line(
    df,
    x="created_at",
    y="size_mb",
    labels={"created_at": "Date", "size_mb": "Size (MB)"},
    markers=True,
    hover_data=["commit_sha", "size_human"],
)

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Size (MB)",
    hovermode="closest",
)

st.plotly_chart(fig, width="stretch")

# Create a table with the data
st.subheader("Wheel Size Details")

history_df = df.sort_values("created_at", ascending=False)

st.dataframe(
    history_df[["created_at", "commit_sha", "size_human", "run_url", "commit_url"]],
    width="stretch",
    column_config={
        "created_at": st.column_config.DatetimeColumn("Date", format="MMM DD, YYYY"),
        "commit_sha": st.column_config.TextColumn("Commit"),
        "size_human": st.column_config.TextColumn("Size"),
        "run_url": st.column_config.LinkColumn("Workflow Run", display_text="View Run"),
        "commit_url": st.column_config.LinkColumn("Commit", display_text="View Commit"),
    },
    hide_index=True,
)

# Add a section to show size changes
if len(df) > 1:
    st.subheader("Size Changes")

    # Calculate size changes between consecutive wheel builds
    df_sorted = df.sort_values("created_at").reset_index(drop=True)
    df_sorted["prev_size"] = df_sorted["size_bytes"].shift(1)
    df_sorted["size_change"] = df_sorted["size_bytes"] - df_sorted["prev_size"]
    df_sorted["size_change_percent"] = (df_sorted["size_change"] / df_sorted["prev_size"]) * 100

    # Filter out the first row (which has NaN for changes)
    df_changes = df_sorted.dropna(subset=["size_change"]).copy()

    if not df_changes.empty:
        # Now that NaNs are removed, compute human-readable size changes
        df_changes["size_change_human"] = df_changes["size_change"].apply(
            lambda x: f"+{humanize.naturalsize(x, binary=True)}" if x > 0 else humanize.naturalsize(x, binary=True)
        )
        # Sort by absolute size change
        df_changes = df_changes.sort_values("size_change", key=abs, ascending=False)

        # Create a bar chart of the top size changes
        fig_changes = px.bar(
            df_changes.head(10),
            x="commit_sha",
            y="size_change_percent",
            labels={"commit_sha": "Commit", "size_change_percent": "Size Change (%)"},
            hover_data=["size_change_human", "created_at"],
            color="size_change",
            color_continuous_scale=["red", "gray", "green"],
        )

        fig_changes.update_layout(
            xaxis_title="Commit",
            yaxis_title="Size Change (%)",
            coloraxis_showscale=False,
        )

        st.plotly_chart(fig_changes, width="stretch")

        # Show a table of significant changes
        significant_changes = df_changes[abs(df_changes["size_change_percent"]) > 0.5].copy()

        if not significant_changes.empty:
            st.caption("Significant size changes (>0.5%)")

            st.dataframe(
                significant_changes[
                    [
                        "created_at",
                        "commit_sha",
                        "size_human",
                        "size_change_human",
                        "size_change_percent",
                        "commit_url",
                    ]
                ],
                width="stretch",
                column_config={
                    "created_at": st.column_config.DatetimeColumn("Date", format="MMM DD, YYYY"),
                    "commit_sha": st.column_config.TextColumn("Commit"),
                    "size_human": st.column_config.TextColumn("Size"),
                    "size_change_human": st.column_config.TextColumn("Change"),
                    "size_change_percent": st.column_config.NumberColumn("Change (%)", format="%.2f%%"),
                    "commit_url": st.column_config.LinkColumn("Commit", display_text="View Commit"),
                },
                hide_index=True,
            )
