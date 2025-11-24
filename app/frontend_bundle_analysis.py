import json
import zipfile
import io
from datetime import datetime, timedelta

import pandas as pd
import altair as alt
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
import humanize

from app.utils.github_utils import (
    download_artifact,
    fetch_artifacts,
    fetch_pr_info,
    fetch_workflow_runs,
    fetch_workflow_runs_for_commit,
)

st.set_page_config(page_title="Frontend Bundle Analysis", page_icon="📦", layout="wide")

title_row = st.container(
    horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"
)
with title_row:
    st.title("📦 Frontend Bundle Analysis")
    if st.button(":material/refresh: Refresh Data", type="tertiary"):
        fetch_workflow_runs.clear()


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


def format_bytes(size):
    return humanize.naturalsize(size, binary=True)


ASSET_JS_EXTENSIONS = (".js", ".mjs", ".cjs")
ASSET_CSS_EXTENSIONS = (".css",)


def get_asset_category(filename):
    if not filename:
        return "other"

    normalized = filename.split("?", 1)[0].lower()

    if normalized.endswith(ASSET_JS_EXTENSIONS):
        return "js"

    if normalized.endswith(ASSET_CSS_EXTENSIONS):
        return "css"

    return "other"


def compute_bundle_metrics(bundle_data):
    metrics = {
        "total_parsed": 0,
        "total_gzip": 0,
        "total_brotli": 0,
        "entry_parsed": 0,
        "entry_gzip": 0,
        "entry_brotli": 0,
        "asset_js_gzip": 0,
        "asset_css_gzip": 0,
        "asset_other_gzip": 0,
    }

    for item in bundle_data:
        metrics["total_parsed"] += item.get("parsedSize", 0)
        metrics["total_gzip"] += item.get("gzipSize", 0)
        metrics["total_brotli"] += item.get("brotliSize", 0)

        if item.get("isEntry"):
            metrics["entry_parsed"] += item.get("parsedSize", 0)
            metrics["entry_gzip"] += item.get("gzipSize", 0)
            metrics["entry_brotli"] += item.get("brotliSize", 0)

        if item.get("isAsset"):
            category = get_asset_category(
                item.get("filename") or item.get("label") or ""
            )
            asset_key = f"asset_{category}_gzip"
            if asset_key in metrics:
                metrics[asset_key] += item.get("gzipSize", 0)

    return metrics


def extract_bundle_metrics_from_artifacts(artifacts, include_bundle_data=False):
    json_artifact = next(
        (
            artifact
            for artifact in artifacts
            if artifact["name"] == "bundle_analysis_json"
        ),
        None,
    )

    if not json_artifact:
        return None

    content = download_artifact(json_artifact["archive_download_url"])
    if not content:
        return None

    bundle_data = process_bundle_artifact(content)
    if not bundle_data:
        return (None, None) if include_bundle_data else None

    metrics = compute_bundle_metrics(bundle_data)

    if include_bundle_data:
        return metrics, bundle_data

    return metrics


def get_html_artifact_urls(run, artifacts):
    html_artifact = next(
        (
            artifact
            for artifact in artifacts
            if artifact["name"] == "bundle_analysis_html"
        ),
        None,
    )

    if not html_artifact:
        return None, None

    html_artifact_url = html_artifact["archive_download_url"]
    html_report_url = f"https://github.com/streamlit/streamlit/actions/runs/{run['id']}/artifacts/{html_artifact['id']}"
    return html_artifact_url, html_report_url


def build_bundle_record(run, metrics, html_artifact_url=None, html_report_url=None):
    return {
        "run_id": run["id"],
        "created_at": run["created_at"],
        "commit_sha": run["head_sha"],
        "commit_url": f"https://github.com/streamlit/streamlit/commit/{run['head_sha']}",
        "run_url": run["html_url"],
        "html_artifact_url": html_artifact_url,
        "html_report_url": html_report_url,
        **metrics,
    }


def get_bundle_record_for_run(run, include_bundle_data=False):
    artifacts = fetch_artifacts(run["id"])

    if include_bundle_data:
        extraction = extract_bundle_metrics_from_artifacts(
            artifacts, include_bundle_data=True
        )
        metrics, bundle_data = extraction if extraction else (None, None)
    else:
        metrics = extract_bundle_metrics_from_artifacts(artifacts)
        bundle_data = None

    if not metrics:
        return (None, None) if include_bundle_data else None

    html_artifact_url, html_report_url = get_html_artifact_urls(run, artifacts)
    record = build_bundle_record(run, metrics, html_artifact_url, html_report_url)

    if include_bundle_data:
        return record, bundle_data

    return record


def format_delta_bytes(current, baseline):
    delta = current - baseline
    if delta == 0:
        return "0 B"
    prefix = "+" if delta > 0 else "-"
    return f"{prefix}{format_bytes(abs(delta))}"


def display_bundle_report(html_artifact_url, title):
    if not html_artifact_url:
        st.warning("No HTML report available for this run.")
        return

    with st.spinner(f"Downloading {title}..."):
        html_content = get_html_report_content(html_artifact_url)

    if html_content:
        components.html(html_content, height=800, scrolling=True)
    else:
        st.error("Failed to download or parse HTML report.")


def build_treemap_dataframe(bundle_data):
    if not bundle_data:
        return pd.DataFrame()

    rows = []
    for item in bundle_data:
        label = (
            item.get("label")
            or item.get("name")
            or item.get("file")
            or item.get("fileName")
            or item.get("chunkName")
            or item.get("id")
            or "Unknown"
        )
        if isinstance(label, str) and "/" in label:
            label = label.split("/")[-1]

        rows.append(
            {
                "Category": "Entry Chunks"
                if item.get("isEntry")
                else "Async/Lazy Chunks",
                "Label": label,
                "Size": item.get("parsedSize") or item.get("gzipSize") or 0,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.groupby(["Category", "Label"], as_index=False)["Size"].sum()
    df["Size (Human)"] = df["Size"].apply(format_bytes)
    return df


def render_bundle_treemap(title, bundle_data):
    df = build_treemap_dataframe(bundle_data)
    if df.empty:
        st.warning(f"No bundle data available for {title.lower()}.")
        return

    fig = px.treemap(
        df,
        path=["Category", "Label"],
        values="Size",
        color="Size",
        color_continuous_scale="Blues",
        hover_data={"Size (Human)": True},
    )
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Size: %{customdata[0]}<extra></extra>"
    )

    st.markdown(f"**{title}**")
    st.plotly_chart(fig, width="stretch")


def display_pr_bundle_comparison(
    pr_bundle, develop_bundle, pr_bundle_chunks, develop_bundle_chunks, pr_number
):
    st.subheader("PR Bundle Comparison")

    st.markdown(
        f"**PR Commit:** [{pr_bundle['commit_sha'][:7]}]({pr_bundle['commit_url']}) | "
        f"**Develop Commit:** [{develop_bundle['commit_sha'][:7]}]({develop_bundle['commit_url']})  \n"
        f"**PR Workflow Run:** [View Run]({pr_bundle['run_url']}) | "
        f"**Develop Workflow Run:** [View Run]({develop_bundle['run_url']})"
    )

    metric_groups = [
        [
            (
                "Total Size (gzip)",
                "total_gzip",
                "Total size of all JavaScript files after Gzip compression. This approximates the download size.",
            ),
            (
                "Entry Size (gzip)",
                "entry_gzip",
                "Size of the entry point chunks after Gzip compression. Smaller values improve initial load time.",
            ),
        ],
        [
            (
                "Total Size (brotli)",
                "total_brotli",
                "Total size of all JavaScript files after Brotli compression.",
            ),
            (
                "Entry Size (brotli)",
                "entry_brotli",
                "Size of the entry point chunks after Brotli compression.",
            ),
        ],
        [
            (
                "Total Size (parsed)",
                "total_parsed",
                "Total size of the JavaScript code after decompression. Impacts parsing and execution time.",
            ),
            (
                "Entry Size (parsed)",
                "entry_parsed",
                "Size of the entry point chunks after decompression.",
            ),
        ],
    ]

    cols = st.columns(3)
    for col, group in zip(cols, metric_groups):
        with col:
            for label, key, help_text in group:
                st.metric(
                    label,
                    format_bytes(pr_bundle[key]),
                    format_delta_bytes(pr_bundle[key], develop_bundle[key]),
                    delta_color="inverse",
                    help=help_text,
                    border=True,
                )

    st.markdown("**Asset Size Breakdown**")
    asset_cols = st.columns(3)
    asset_metric_groups = [
        (
            "JS Asset Size (gzip)",
            "asset_js_gzip",
            "Total Size (gzip) of emitted JavaScript assets (including standalone chunks).",
        ),
        (
            "CSS Asset Size (gzip)",
            "asset_css_gzip",
            "Total Size (gzip) of emitted CSS assets.",
        ),
        (
            "Other Asset Size (gzip)",
            "asset_other_gzip",
            "Total Size (gzip) of all remaining asset files (images, fonts, etc.).",
        ),
    ]

    for col, (label, key, help_text) in zip(asset_cols, asset_metric_groups):
        with col:
            st.metric(
                label,
                format_bytes(pr_bundle[key]),
                format_delta_bytes(pr_bundle[key], develop_bundle[key]),
                delta_color="inverse",
                help=help_text,
                border=True,
            )

    col1, col2 = st.columns(2)

    with col1:
        if pr_bundle["html_report_url"]:
            st.link_button(
                label=":material/download: Download PR Bundle Report",
                url=pr_bundle["html_report_url"],
                width="stretch",
            )

    with col2:
        if develop_bundle["html_report_url"]:
            st.link_button(
                label=":material/download: Download Develop Bundle Report",
                url=develop_bundle["html_report_url"],
                width="stretch",
            )

    st.subheader("Bundle Composition Treemaps")
    treemap_col1, treemap_col2 = st.columns(2)

    with treemap_col1:
        render_bundle_treemap("PR Bundle", pr_bundle_chunks)

    with treemap_col2:
        render_bundle_treemap("Develop Bundle", develop_bundle_chunks)

    st.subheader("Bundle Analysis Reports")
    report_col1, report_col2 = st.columns(2)

    with report_col1:
        st.markdown("**PR Bundle Report**")
        if pr_bundle["html_artifact_url"]:
            display_bundle_report(
                pr_bundle["html_artifact_url"], "the PR bundle analysis report"
            )
        else:
            st.warning("No HTML report available for the PR run.")

    with report_col2:
        st.markdown("**Develop Bundle Report**")
        if develop_bundle["html_artifact_url"]:
            display_bundle_report(
                develop_bundle["html_artifact_url"],
                "the develop bundle analysis report",
            )
        else:
            st.warning("No HTML report available for the develop run.")


def handle_pr_mode(pr_number):
    with st.spinner(f"Fetching data for PR #{pr_number}..."):
        pr_info = fetch_pr_info(pr_number)

    if not pr_info:
        st.error(f"Could not fetch information for PR #{pr_number}.")
        return

    head_sha = pr_info["head"]["sha"]

    with st.spinner("Fetching PR workflow runs..."):
        pr_runs = fetch_workflow_runs_for_commit(head_sha, "pr-preview.yml")

    if not pr_runs:
        st.error(
            f"No successful `pr-preview.yml` workflow runs found for PR commit {head_sha[:7]}."
        )
        return

    pr_bundle = None
    pr_bundle_chunks = None
    for run in pr_runs:
        record = get_bundle_record_for_run(run, include_bundle_data=True)
        if record and record[0]:
            pr_bundle, pr_bundle_chunks = record
            break

    if not pr_bundle:
        st.error("Could not extract bundle metrics from the PR workflow artifacts.")
        return

    with st.spinner("Fetching latest develop workflow run..."):
        develop_runs = fetch_workflow_runs("pr-preview.yml", limit=1)

    if not develop_runs:
        st.error("No successful develop workflow runs found for `pr-preview.yml`.")
        return

    develop_record = get_bundle_record_for_run(
        develop_runs[0], include_bundle_data=True
    )
    if not develop_record or not develop_record[0]:
        st.error(
            "Could not extract bundle metrics from the latest develop workflow run."
        )
        return

    develop_bundle, develop_bundle_chunks = develop_record

    display_pr_bundle_comparison(
        pr_bundle, develop_bundle, pr_bundle_chunks, develop_bundle_chunks, pr_number
    )


query_params = st.query_params
pr_number = query_params.get("pr")
if isinstance(pr_number, list):
    pr_number = pr_number[0]

if pr_number:
    st.caption(
        f"Comparing bundle metrics for [PR #{pr_number}](https://github.com/streamlit/streamlit/pull/{pr_number}) against the latest develop run."
    )
    handle_pr_mode(pr_number)
    st.stop()

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


# Fetch runs
# Analyze frontend bundle is in pr-preview.yml
runs = fetch_workflow_runs(
    "pr-preview.yml", limit=limit, since=since.date() if since else None
)

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
        metrics = extract_bundle_metrics_from_artifacts(artifacts)
        if not metrics:
            continue

        html_artifact_url, html_report_url = get_html_artifact_urls(run, artifacts)

        data.append(
            build_bundle_record(
                run,
                metrics,
                html_artifact_url=html_artifact_url,
                html_report_url=html_report_url,
            )
        )

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

with col1:
    st.metric(
        "Total Size (gzip)",
        format_bytes(latest["total_gzip"]),
        delta=format_bytes(
            calculate_delta(latest["total_gzip"], start_run["total_gzip"])
        ),
        delta_color="inverse",
        help="Total size of all JavaScript files after Gzip compression. This is a good approximation of the download size for most users.",
        border=True,
        chart_data=sparkline_data["total_gzip"],
        chart_type="area",
    )

    st.metric(
        "Entry Size (gzip)",
        format_bytes(latest["entry_gzip"]),
        delta=format_bytes(
            calculate_delta(latest["entry_gzip"], start_run["entry_gzip"])
        ),
        delta_color="inverse",
        help="Size of the entry point chunks (initial load) after Gzip compression. Smaller entry size means faster initial page load.",
        border=True,
        chart_data=sparkline_data["entry_gzip"],
        chart_type="area",
    )

with col2:
    st.metric(
        "Total Size (brotli)",
        format_bytes(latest["total_brotli"]),
        delta=format_bytes(
            calculate_delta(latest["total_brotli"], start_run["total_brotli"])
        ),
        delta_color="inverse",
        help="Total size of all JavaScript files after Brotli compression. Brotli usually provides better compression than Gzip but is slower to compress.",
        border=True,
        chart_data=sparkline_data["total_brotli"],
        chart_type="area",
    )

    st.metric(
        "Entry Size (brotli)",
        format_bytes(latest["entry_brotli"]),
        delta=format_bytes(
            calculate_delta(latest["entry_brotli"], start_run["entry_brotli"])
        ),
        delta_color="inverse",
        help="Size of the entry point chunks (initial load) after Brotli compression.",
        border=True,
        chart_data=sparkline_data["entry_brotli"],
        chart_type="area",
    )

with col3:
    st.metric(
        "Total Size (parsed)",
        format_bytes(latest["total_parsed"]),
        delta=format_bytes(
            calculate_delta(latest["total_parsed"], start_run["total_parsed"])
        ),
        delta_color="inverse",
        help="Total size of the JavaScript code after decompression (as it exists in memory). This affects parsing and execution time in the browser.",
        border=True,
        chart_data=sparkline_data["total_parsed"],
        chart_type="area",
    )

    st.metric(
        "Entry Size (parsed)",
        format_bytes(latest["entry_parsed"]),
        delta=format_bytes(
            calculate_delta(latest["entry_parsed"], start_run["entry_parsed"])
        ),
        delta_color="inverse",
        help="Size of the entry point chunks after decompression.",
        border=True,
        chart_data=sparkline_data["entry_parsed"],
        chart_type="area",
    )

st.subheader("Asset Size Breakdown")
asset_cols_overview = st.columns(3)
asset_metric_configs = [
    (
        "JS Asset Size (gzip)",
        "asset_js_gzip",
        "Total Size (gzip) of emitted JavaScript assets (including standalone chunks).",
    ),
    (
        "CSS Asset Size (gzip)",
        "asset_css_gzip",
        "Total Size (gzip) of emitted CSS assets.",
    ),
    (
        "Other Asset Size (gzip)",
        "asset_other_gzip",
        "Total Size (gzip) of all remaining asset files (images, fonts, etc.).",
    ),
]

for col, (label, key, help_text) in zip(asset_cols_overview, asset_metric_configs):
    with col:
        st.metric(
            label,
            format_bytes(latest[key]),
            delta=format_bytes(calculate_delta(latest[key], start_run[key])),
            delta_color="inverse",
            help=help_text,
            border=True,
            chart_data=sparkline_data[key],
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
        value_name="Size",
    )

    # Rename categories for legend
    chart_data["Category"] = chart_data["Category"].replace(
        {
            f"total_{metric_suffix}": "Total",
            f"entry_{metric_suffix}": "Entry",
        }
    )

    # Add human readable size for tooltip
    chart_data["Size (Human)"] = chart_data["Size"].apply(lambda x: format_bytes(x))

    chart = (
        alt.Chart(chart_data)
        .mark_line(point=True)
        .encode(
            x=alt.X("created_at", title="Date"),
            y=alt.Y("Size", title="Size (Bytes)"),
            color="Category",
            tooltip=[
                alt.Tooltip("created_at", title="Date", format="%Y-%m-%d %H:%M"),
                alt.Tooltip("Category", title="Type"),
                alt.Tooltip("Size (Human)", title="Size"),
                alt.Tooltip("commit_sha", title="Commit"),
            ],
        )
        .properties(title=title)
        .interactive()
    )
    return chart


with tab_gzip:
    st.altair_chart(
        create_trend_chart(df, "gzip", "Gzip Size Over Time"),
        width="stretch",
    )

with tab_brotli:
    st.altair_chart(
        create_trend_chart(df, "brotli", "Brotli Size Over Time"),
        width="stretch",
    )

with tab_parsed:
    st.altair_chart(
        create_trend_chart(df, "parsed", "Parsed Size Over Time"),
        width="stretch",
    )


# Detailed Data Table
st.subheader("Bundle Size History")
st.caption(
    ":material/keyboard_arrow_down: Select a row to view the Bundle Analysis HTML report."
)

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
display_df["asset_js_gzip_change"] = display_df["asset_js_gzip"].pct_change(periods=-1)
display_df["asset_css_gzip_change"] = display_df["asset_css_gzip"].pct_change(
    periods=-1
)
display_df["asset_other_gzip_change"] = display_df["asset_other_gzip"].pct_change(
    periods=-1
)


# Add formatted columns for display
for col in [
    "total_gzip",
    "entry_gzip",
    "total_brotli",
    "entry_brotli",
    "total_parsed",
    "entry_parsed",
    "asset_js_gzip",
    "asset_css_gzip",
    "asset_other_gzip",
]:
    display_df[f"{col}_fmt"] = display_df[col].apply(format_bytes)

# Configure columns
column_config = {
    "created_at": st.column_config.DatetimeColumn("Date", format="distance"),
    "total_gzip_fmt": st.column_config.TextColumn("Total Gzip"),
    "total_gzip_change": st.column_config.NumberColumn(
        "Total Gzip Change", format="percent"
    ),
    "entry_gzip_fmt": st.column_config.TextColumn("Entry Gzip"),
    "entry_gzip_change": st.column_config.NumberColumn(
        "Entry Gzip Change", format="percent"
    ),
    "total_brotli_fmt": st.column_config.TextColumn("Total Brotli"),
    "total_brotli_change": st.column_config.NumberColumn(
        "Total Brotli Change", format="percent"
    ),
    "entry_brotli_fmt": st.column_config.TextColumn("Entry Brotli"),
    "entry_brotli_change": st.column_config.NumberColumn(
        "Entry Brotli Change", format="percent"
    ),
    "total_parsed_fmt": st.column_config.TextColumn("Total Parsed"),
    "total_parsed_change": st.column_config.NumberColumn(
        "Total Parsed Change", format="percent"
    ),
    "entry_parsed_fmt": st.column_config.TextColumn("Entry Parsed"),
    "entry_parsed_change": st.column_config.NumberColumn(
        "Entry Parse Change", format="percent"
    ),
    "asset_js_gzip_fmt": st.column_config.TextColumn("JS Asset Gzip"),
    "asset_js_gzip_change": st.column_config.NumberColumn(
        "JS Asset Gzip Change", format="percent"
    ),
    "asset_css_gzip_fmt": st.column_config.TextColumn("CSS Asset Gzip"),
    "asset_css_gzip_change": st.column_config.NumberColumn(
        "CSS Asset Gzip Change", format="percent"
    ),
    "asset_other_gzip_fmt": st.column_config.TextColumn("Other Asset Gzip"),
    "asset_other_gzip_change": st.column_config.NumberColumn(
        "Other Asset Gzip Change", format="percent"
    ),
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
    display_df[
        [
            "created_at",
            "total_gzip_fmt",
            "total_gzip_change",
            "entry_gzip_fmt",
            "entry_gzip_change",
            "total_brotli_fmt",
            "total_brotli_change",
            "entry_brotli_fmt",
            "entry_brotli_change",
            "total_parsed_fmt",
            "total_parsed_change",
            "entry_parsed_fmt",
            "entry_parsed_change",
            "asset_js_gzip_fmt",
            "asset_js_gzip_change",
            "asset_css_gzip_fmt",
            "asset_css_gzip_change",
            "asset_other_gzip_fmt",
            "asset_other_gzip_change",
            "run_url",
            "commit_url",
            "html_report_url",
        ]
    ],
    column_config=column_config,
    hide_index=True,
    selection_mode="single-row",
    on_select="rerun",
    width="stretch",
)

if selection.selection.rows:
    row_idx = selection.selection.rows[0]
    selected_row = display_df.iloc[row_idx]

    if selected_row["html_artifact_url"]:
        st.subheader("Bundle Analysis Report")
        display_bundle_report(
            selected_row["html_artifact_url"], "the selected bundle analysis report"
        )
    else:
        st.warning("No HTML report available for this run.")
