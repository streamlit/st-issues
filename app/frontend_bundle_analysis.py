import json
import zipfile
import io
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
import humanize

from app.utils.github_utils import (
    fetch_workflow_runs,
    fetch_artifacts,
    download_artifact,
)

st.set_page_config(page_title="Frontend Bundle Analysis", page_icon="📦", layout="wide")

st.title("📦 Frontend Bundle Analysis")
st.caption(
    "This page visualizes the frontend bundle size metrics tracked in the PR preview workflow."
)

# Sidebar
time_period = st.sidebar.selectbox(
    "Time period",
    options=["All time", "Last 7 days", "Last 30 days", "Last 90 days"],
    index=0,
)
limit = st.sidebar.slider(
    "Number of workflow runs",
    min_value=50,
    max_value=250,
    value=50,
    step=50,
)

# Calculate date
if time_period == "Last 7 days":
    since = datetime.now() - timedelta(days=7)
elif time_period == "Last 30 days":
    since = datetime.now() - timedelta(days=30)
elif time_period == "Last 90 days":
    since = datetime.now() - timedelta(days=90)
else:
    since = None


@st.cache_data(show_spinner=False)
def process_bundle_artifact(content):
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            for name in z.namelist():
                if name.endswith(".json"):
                    with z.open(name) as f:
                        bundle_data = json.load(f)
                        return bundle_data
    except Exception:
        return None
    return None


@st.cache_data(show_spinner=False)
def get_html_report_content(url):
    content = download_artifact(url)
    if content:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                for name in z.namelist():
                    if name.endswith(".html"):
                        with z.open(name) as f:
                            return f.read().decode("utf-8")
        except Exception:
            return None
    return None


# Fetch runs
# Analyze frontend bundle is in pr-preview.yml
runs = fetch_workflow_runs("pr-preview.yml", limit=limit, since=since.date() if since else None)

if not runs:
    st.warning("No workflow runs found.")
    st.stop()

data = []

with st.spinner("Processing bundle analysis data..."):
    progress_bar = st.progress(0)

    # We need to fetch artifacts for each run
    # To avoid too many requests if we have many runs, we rely on cache in fetch_artifacts

    for i, run in enumerate(runs):
        progress_bar.progress((i + 1) / len(runs))

        # We only want to process successful runs that might have the artifact
        if run["status"] != "completed" or run["conclusion"] != "success":
            continue

        artifacts = fetch_artifacts(run["id"])
        json_artifact = next((a for a in artifacts if a["name"] == "bundle_analysis_json"), None)
        html_artifact = next((a for a in artifacts if a["name"] == "bundle_analysis_html"), None)

        if json_artifact:
            content = download_artifact(json_artifact["archive_download_url"])
            if content:
                bundle_data = process_bundle_artifact(content)

                if bundle_data:
                    # Calculate metrics
                    metrics = {
                        "total_parsed": 0, "total_gzip": 0, "total_brotli": 0,
                        "entry_parsed": 0, "entry_gzip": 0, "entry_brotli": 0,
                    }

                    for item in bundle_data:
                        # Total
                        metrics["total_parsed"] += item.get("parsedSize", 0)
                        metrics["total_gzip"] += item.get("gzipSize", 0)
                        metrics["total_brotli"] += item.get("brotliSize", 0)

                        # Entry
                        if item.get("isEntry"):
                            metrics["entry_parsed"] += item.get("parsedSize", 0)
                            metrics["entry_gzip"] += item.get("gzipSize", 0)
                            metrics["entry_brotli"] += item.get("brotliSize", 0)

                    html_report_url = None
                    if html_artifact:
                        html_report_url = f"https://github.com/streamlit/streamlit/actions/runs/{run['id']}/artifacts/{html_artifact['id']}"

                    data.append({
                        "run_id": run["id"],
                        "created_at": run["created_at"],
                        "commit_sha": run["head_sha"],
                        "commit_url": f"https://github.com/streamlit/streamlit/commit/{run['head_sha']}",
                        "run_url": run["html_url"],
                        "html_artifact_url": html_artifact["archive_download_url"] if html_artifact else None,
                        "html_report_url": html_report_url,
                        **metrics
                    })

    progress_bar.empty()

if not data:
    st.info("No bundle analysis artifacts found in the recent runs.")
    st.stop()

df = pd.DataFrame(data)
df["created_at"] = pd.to_datetime(df["created_at"])
df = df.sort_values("created_at")

# Display metrics (Latest run)
latest = df.iloc[-1]
# Get the last 20 runs for sparklines
sparkline_data = df.tail(20)

# Calculate delta over the selected period
# We compare the latest run with the first run in the selected period
start_run = df.iloc[0]

def calculate_delta(current, start):
    if start == 0:
        return None
    return current - start

col1, col2, col3 = st.columns(3)

def format_bytes(size):
    return humanize.naturalsize(size, binary=True)

with col1:
    st.metric(
        "Total Gzip Size",
        format_bytes(latest["total_gzip"]),
        delta=format_bytes(calculate_delta(latest["total_gzip"], start_run["total_gzip"])),
        delta_color="inverse",
        help="Total size of all JavaScript files after Gzip compression. This is a good approximation of the download size for most users.",
        border=True,
        chart_data=sparkline_data["total_gzip"],
        chart_type="area",
    )

    st.metric(
        "Entry Gzip Size",
        format_bytes(latest["entry_gzip"]),
        delta=format_bytes(calculate_delta(latest["entry_gzip"], start_run["entry_gzip"])),
        delta_color="inverse",
        help="Size of the entry point chunks (initial load) after Gzip compression. Smaller entry size means faster initial page load.",
        border=True,
        chart_data=sparkline_data["entry_gzip"],
        chart_type="area",
    )

with col2:
    st.metric(
        "Total Brotli Size",
        format_bytes(latest["total_brotli"]),
        delta=format_bytes(calculate_delta(latest["total_brotli"], start_run["total_brotli"])),
        delta_color="inverse",
        help="Total size of all JavaScript files after Brotli compression. Brotli usually provides better compression than Gzip but is slower to compress.",
        border=True,
        chart_data=sparkline_data["total_brotli"],
        chart_type="area",
    )

    st.metric(
        "Entry Brotli Size",
        format_bytes(latest["entry_brotli"]),
        delta=format_bytes(calculate_delta(latest["entry_brotli"], start_run["entry_brotli"])),
        delta_color="inverse",
        help="Size of the entry point chunks (initial load) after Brotli compression.",
        border=True,
        chart_data=sparkline_data["entry_brotli"],
        chart_type="area",
    )

with col3:
    st.metric(
        "Total Parsed Size",
        format_bytes(latest["total_parsed"]),
        delta=format_bytes(calculate_delta(latest["total_parsed"], start_run["total_parsed"])),
        delta_color="inverse",
        help="Total size of the JavaScript code after decompression (as it exists in memory). This affects parsing and execution time in the browser.",
        border=True,
        chart_data=sparkline_data["total_parsed"],
        chart_type="area",
    )

    st.metric(
        "Entry Parsed Size",
        format_bytes(latest["entry_parsed"]),
        delta=format_bytes(calculate_delta(latest["entry_parsed"], start_run["entry_parsed"])),
        delta_color="inverse",
        help="Size of the entry point chunks after decompression.",
        border=True,
        chart_data=sparkline_data["entry_parsed"],
        chart_type="area",
    )


# Charts
st.subheader("Bundle Size Trends")

tab_gzip, tab_brotli, tab_parsed = st.tabs(["Gzip Size", "Brotli Size", "Parsed Size"])

def create_trend_chart(df, metric_suffix, title):
    chart_data = df.melt(
        id_vars=["created_at", "commit_sha"],
        value_vars=[f"total_{metric_suffix}", f"entry_{metric_suffix}"],
        var_name="Category",
        value_name="Size"
    )

    # Rename categories for legend
    chart_data["Category"] = chart_data["Category"].replace({
        f"total_{metric_suffix}": "Total",
        f"entry_{metric_suffix}": "Entry",
    })

    # Add human readable size for tooltip
    chart_data["Size (Human)"] = chart_data["Size"].apply(lambda x: format_bytes(x))

    fig = px.line(
        chart_data,
        x="created_at",
        y="Size",
        color="Category",
        title=title,
        markers=True,
        hover_data=["commit_sha", "Size (Human)"]
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Size (Bytes)",
        hovermode="closest"
    )
    return fig

with tab_gzip:
    st.plotly_chart(create_trend_chart(df, "gzip", "Gzip Size Over Time"), use_container_width=True)

with tab_brotli:
    st.plotly_chart(create_trend_chart(df, "brotli", "Brotli Size Over Time"), use_container_width=True)

with tab_parsed:
    st.plotly_chart(create_trend_chart(df, "parsed", "Parsed Size Over Time"), use_container_width=True)


# Detailed Data Table
st.subheader("Bundle Size History")
st.caption(":material/keyboard_arrow_down: Select a row to view the Bundle Analysis HTML report.")

# Prepare display dataframe
display_df = df.copy()
display_df = display_df.sort_values("created_at", ascending=False)

# Calculate changes
display_df["total_gzip_change"] = display_df["total_gzip"].pct_change(periods=-1)
display_df["entry_gzip_change"] = display_df["entry_gzip"].pct_change(periods=-1)
display_df["total_brotli_change"] = display_df["total_brotli"].pct_change(periods=-1)
display_df["entry_brotli_change"] = display_df["entry_brotli"].pct_change(periods=-1)
display_df["total_parsed_change"] = display_df["total_parsed"].pct_change(periods=-1)
display_df["entry_parsed_change"] = display_df["entry_parsed"].pct_change(periods=-1)


# Add formatted columns for display
for col in ["total_gzip", "entry_gzip", "total_brotli", "entry_brotli", "total_parsed", "entry_parsed"]:
    display_df[f"{col}_fmt"] = display_df[col].apply(format_bytes)

# Configure columns
column_config = {
    "created_at": st.column_config.DatetimeColumn("Date", format="distance"),
    "total_gzip_fmt": st.column_config.TextColumn("Total Gzip"),
    "total_gzip_change": st.column_config.NumberColumn("Total Gzip Change", format="percent"),
    "entry_gzip_fmt": st.column_config.TextColumn("Entry Gzip"),
    "entry_gzip_change": st.column_config.NumberColumn("Entry Gzip Change", format="percent"),
    "total_brotli_fmt": st.column_config.TextColumn("Total Brotli"),
    "total_brotli_change": st.column_config.NumberColumn("Total Brotli Change", format="percent"),
    "entry_brotli_fmt": st.column_config.TextColumn("Entry Brotli"),
    "entry_brotli_change": st.column_config.NumberColumn("Entry Brotli Change", format="percent"),
    "total_parsed_fmt": st.column_config.TextColumn("Total Parsed"),
    "total_parsed_change": st.column_config.NumberColumn("Total Parsed Change", format="percent"),
    "entry_parsed_fmt": st.column_config.TextColumn("Entry Parsed"),
    "entry_parsed_change": st.column_config.NumberColumn("Entry Parse Change", format="percent"),
    "run_url": st.column_config.LinkColumn("Workflow Run", display_text="View Run"),
    "commit_url": st.column_config.LinkColumn(
            "Commit",
            display_text="https://github.com/streamlit/streamlit/commit/([a-f0-9]{7}).*",
    ),
    "html_report_url": st.column_config.LinkColumn(
        "HTML Report",
        display_text="Download",
        help="Download the full HTML bundle analysis report",
    ),
}

selection = st.dataframe(
    display_df[[
        "created_at",
        "total_gzip_fmt", "total_gzip_change",
        "entry_gzip_fmt", "entry_gzip_change",
        "total_brotli_fmt", "total_brotli_change",
        "entry_brotli_fmt", "entry_brotli_change",
        "total_parsed_fmt", "total_parsed_change",
        "entry_parsed_fmt", "entry_parsed_change",
        "run_url", "commit_url", "html_report_url",
    ]],
    column_config=column_config,
    hide_index=True,
    selection_mode="single-row",
    on_select="rerun",
    use_container_width=True
)

if selection.selection.rows:
    row_idx = selection.selection.rows[0]
    selected_row = display_df.iloc[row_idx]

    if selected_row["html_artifact_url"]:
        st.subheader("Bundle Analysis Report")
        with st.spinner("Downloading report..."):
            html_content = get_html_report_content(selected_row["html_artifact_url"])
            if html_content:
                components.html(html_content, height=800, scrolling=True)
            else:
                st.error("Failed to download or parse HTML report.")
    else:
        st.warning("No HTML report available for this run.")
