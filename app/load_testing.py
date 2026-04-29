from __future__ import annotations

import json
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any
from zipfile import ZipFile

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from app.utils.github_utils import (
    download_artifact,
    fetch_artifacts,
    fetch_pr_info,
    fetch_workflow_runs,
    fetch_workflow_runs_for_commit,
    get_headers,
)

st.set_page_config(page_title="Load testing", page_icon="⚡", layout="wide")

LOAD_TESTING_WORKFLOW = "load-testing.yml"

query_params = st.query_params
pr_number_param = query_params.get("pr")
pr_number = (pr_number_param[0] if pr_number_param else None) if isinstance(pr_number_param, list) else pr_number_param

title_row = st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center")
with title_row:
    st.title("⚡ Load testing")
    if st.button(":material/refresh: Refresh Data", type="tertiary"):
        fetch_workflow_runs.clear()

if pr_number:
    st.caption(
        f"Comparing load test stats for [PR #{pr_number}](https://github.com/streamlit/streamlit/pull/{pr_number}) "
        "against the latest develop run."
    )
else:
    st.caption(
        "This page visualizes load testing results over time, based on the "
        f"`{LOAD_TESTING_WORKFLOW}` workflow runs on the develop branch."
    )

# Sidebar controls
if pr_number:
    since_date: datetime | None = None
    workflow_runs_limit = 1
else:
    time_period = st.sidebar.selectbox(
        "Time period",
        options=["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
        help="The time period to display load test results for.",
        index=3,
    )
    workflow_runs_limit = st.sidebar.slider(
        "Number of workflow runs",
        min_value=20,
        max_value=200,
        value=50,
        step=10,
        help="Number of workflow runs (commits to develop) to include.",
    )

    if time_period == "Last 7 days":
        since_date = datetime.now() - timedelta(days=7)
    elif time_period == "Last 30 days":
        since_date = datetime.now() - timedelta(days=30)
    elif time_period == "Last 90 days":
        since_date = datetime.now() - timedelta(days=90)
    else:
        since_date = None


def _parse_load_test_payload(content: bytes) -> dict[str, Any] | None:
    """Try to parse load test JSON from raw bytes or a zip archive."""
    # Non-archived artifacts (archive: false) are raw JSON
    try:
        payload = json.loads(content)
        if isinstance(payload, dict) and "scenarios" in payload:
            return payload
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass

    # Archived artifacts are wrapped in a zip
    try:
        with ZipFile(BytesIO(content)) as zip_file:
            for name in zip_file.namelist():
                if name.endswith(".json"):
                    with zip_file.open(name) as f:
                        return json.load(f)
    except Exception:  # noqa: S110
        pass

    return None


@st.cache_data(show_spinner=False)
def _download_artifact_raw(artifact_url: str) -> bytes | None:
    """Download an artifact, handling both redirect-based and direct responses."""
    try:
        resp = requests.get(
            artifact_url,
            headers=get_headers(),
            timeout=60,
            allow_redirects=True,
        )
        if resp.status_code == 200:
            return resp.content
    except requests.RequestException:
        pass
    return None


@st.cache_data(show_spinner=False)
def get_load_test_results(run_id: int) -> dict[str, Any] | None:
    """Download and parse load-test-results.json from a workflow run."""
    artifacts = fetch_artifacts(run_id)

    results_artifact = None
    for artifact in artifacts:
        if "load-test" in artifact["name"] or artifact["name"] == "artifact":
            results_artifact = artifact
            break

    if not results_artifact:
        return None

    # Try the standard zip download first (works for archived artifacts)
    artifact_content = download_artifact(results_artifact["archive_download_url"])
    if artifact_content:
        result = _parse_load_test_payload(artifact_content)
        if result:
            return result

    # For non-archived artifacts (archive: false), the /zip endpoint may not
    # return a zip. Try downloading with redirects enabled as a fallback.
    artifact_content = _download_artifact_raw(results_artifact["archive_download_url"])
    if artifact_content:
        result = _parse_load_test_payload(artifact_content)
        if result:
            return result

    # Last resort: try the artifact URL directly (some API versions expose a
    # direct download URL for non-archived artifacts).
    artifact_url = results_artifact.get("url", "")
    if artifact_url:
        artifact_content = _download_artifact_raw(artifact_url)
        if artifact_content:
            result = _parse_load_test_payload(artifact_content)
            if result:
                return result

    return None


def flatten_scenario_records(run: dict[str, Any], results: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten scenario data into per-scenario records for a single run."""
    metadata = results.get("metadata", {})
    git_sha = metadata.get("git_sha", run["head_sha"])
    records = []

    for scenario in results.get("scenarios", []):
        server = scenario.get("server_metrics", {})
        session = scenario.get("session_metrics", {})
        initial_load = session.get("initial_load_time_ms", {})
        rerun = session.get("rerun_time_ms", {})

        records.append(
            {
                "run_id": run["id"],
                "created_at": datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                "commit_sha": git_sha[:7],
                "commit_url": f"https://github.com/streamlit/streamlit/commit/{git_sha}",
                "run_url": run["html_url"],
                "runner": metadata.get("runner", ""),
                "scenario": scenario.get("scenario", "unknown"),
                "concurrent_users": scenario.get("concurrent_users", 0),
                "duration_seconds": scenario.get("duration_seconds", 0),
                # Server metrics
                "memory_peak_mb": server.get("memory_rss_mb_peak", 0),
                "memory_growth_mb": server.get("memory_rss_mb_growth", 0),
                "memory_avg_mb": server.get("memory_rss_mb_avg", 0),
                "cpu_avg_pct": server.get("cpu_percent_avg", 0),
                "cpu_peak_pct": server.get("cpu_percent_peak", 0),
                "thread_count_max": server.get("thread_count_max", 0),
                # Session metrics
                "total_sessions": session.get("total_sessions", 0),
                "sessions_completed": session.get("sessions_completed", 0),
                "sessions_failed": session.get("sessions_failed", 0),
                "error_count": len(session.get("errors", [])),
                # Initial load time
                "initial_load_p50_ms": initial_load.get("p50", 0),
                "initial_load_p95_ms": initial_load.get("p95", 0),
                "initial_load_p99_ms": initial_load.get("p99", 0),
                "initial_load_mean_ms": initial_load.get("mean", 0),
                "initial_load_min_ms": initial_load.get("min", 0),
                "initial_load_max_ms": initial_load.get("max", 0),
                # Rerun time
                "rerun_p50_ms": rerun.get("p50", 0),
                "rerun_p95_ms": rerun.get("p95", 0),
                "rerun_p99_ms": rerun.get("p99", 0),
                "rerun_mean_ms": rerun.get("mean", 0),
                "rerun_min_ms": rerun.get("min", 0),
                "rerun_max_ms": rerun.get("max", 0),
            }
        )

    return records


def get_load_test_run_data(run: dict[str, Any]) -> dict[str, Any] | None:
    """Return parsed load test data and flattened records for a workflow run."""
    results = get_load_test_results(run["id"])
    if not results:
        return None

    records = flatten_scenario_records(run, results)
    if not records:
        return None

    return {
        "run": run,
        "results": results,
        "records": records,
    }


def get_latest_develop_load_test() -> dict[str, Any] | None:
    """Get load test data for the latest successful workflow run on develop."""
    latest_runs = fetch_workflow_runs(LOAD_TESTING_WORKFLOW, limit=1)
    if not latest_runs:
        st.error(f"No recent successful `{LOAD_TESTING_WORKFLOW}` runs found on develop.")
        return None

    load_test_data = get_load_test_run_data(latest_runs[0])
    if not load_test_data:
        st.error("Could not fetch load test results for the latest develop run.")
        return None

    return load_test_data


def get_pr_load_test(pr_info: dict[str, Any]) -> dict[str, Any] | None:
    """Get load test data for a PR's head commit."""
    head_sha = pr_info["head"]["sha"]
    pr_runs = fetch_workflow_runs_for_commit(head_sha, LOAD_TESTING_WORKFLOW)

    if not pr_runs:
        st.error(f"No successful `{LOAD_TESTING_WORKFLOW}` runs found for PR commit {head_sha[:7]}.")
        return None

    for pr_run in pr_runs:
        load_test_data = get_load_test_run_data(pr_run)
        if load_test_data:
            return load_test_data

    st.error(f"Could not fetch load test results for PR commit {head_sha[:7]}.")
    return None


def summarize_load_test_records(records: list[dict[str, Any]]) -> dict[str, float]:
    """Summarize per-scenario load test records into run-level metrics."""
    run_df = pd.DataFrame(records)
    if run_df.empty:
        return {
            "avg_initial_load_p50_s": 0.0,
            "avg_initial_load_p95_s": 0.0,
            "avg_rerun_p50_ms": 0.0,
            "max_memory_peak_mb": 0.0,
            "total_failed_sessions": 0.0,
        }

    return {
        "avg_initial_load_p50_s": run_df["initial_load_p50_ms"].mean() / 1000,
        "avg_initial_load_p95_s": run_df["initial_load_p95_ms"].mean() / 1000,
        "avg_rerun_p50_ms": run_df["rerun_p50_ms"].mean(),
        "max_memory_peak_mb": run_df["memory_peak_mb"].max(),
        "total_failed_sessions": run_df["sessions_failed"].sum(),
    }


def format_metric_delta(delta: float, unit: str, precision: int) -> str:
    """Format a signed metric delta for st.metric."""
    sign = "+" if delta > 0 else ""
    separator = "" if not unit or unit == "%" else " "
    return f"{sign}{delta:.{precision}f}{separator}{unit}"


def get_comparison_metric_definitions() -> list[tuple[str, str, float, str]]:
    """Return comparison metrics as label, record key, scale divisor, and display unit."""
    return [
        ("Initial load p50", "initial_load_p50_ms", 1000, "s"),
        ("Initial load p95", "initial_load_p95_ms", 1000, "s"),
        ("Initial load p99", "initial_load_p99_ms", 1000, "s"),
        ("Rerun p50", "rerun_p50_ms", 1, "ms"),
        ("Rerun p95", "rerun_p95_ms", 1, "ms"),
        ("Rerun p99", "rerun_p99_ms", 1, "ms"),
        ("Memory peak", "memory_peak_mb", 1, "MB"),
        ("Memory growth", "memory_growth_mb", 1, "MB"),
        ("CPU avg", "cpu_avg_pct", 1, "%"),
        ("CPU peak", "cpu_peak_pct", 1, "%"),
        ("Failed sessions", "sessions_failed", 1, "count"),
        ("Errors", "error_count", 1, "count"),
    ]


def scale_metric_value(value: Any, scale: float) -> float | None:
    """Scale a raw metric value for display."""
    if pd.isna(value):
        return None

    return float(value) / scale


def build_scenario_comparison_df(
    pr_records: list[dict[str, Any]], develop_records: list[dict[str, Any]]
) -> pd.DataFrame:
    """Build a long-form scenario comparison table."""
    pr_df = pd.DataFrame(pr_records)
    develop_df = pd.DataFrame(develop_records)
    if pr_df.empty and develop_df.empty:
        return pd.DataFrame()

    merged_df = pr_df.merge(
        develop_df,
        on="scenario",
        how="outer",
        suffixes=("_pr", "_develop"),
    )

    comparison_records = []
    for _, row in merged_df.iterrows():
        for label, key, scale, unit in get_comparison_metric_definitions():
            pr_display_value = scale_metric_value(row.get(f"{key}_pr"), scale)
            develop_display_value = scale_metric_value(row.get(f"{key}_develop"), scale)

            if pr_display_value is None:
                comparison_records.append(
                    {
                        "Scenario": row["scenario"],
                        "Metric": label,
                        "Unit": unit,
                        "PR": None,
                        "Develop": develop_display_value,
                        "Delta": None,
                        "Delta %": None,
                        "Impact": "Develop only",
                    }
                )
                continue

            if develop_display_value is None:
                comparison_records.append(
                    {
                        "Scenario": row["scenario"],
                        "Metric": label,
                        "Unit": unit,
                        "PR": pr_display_value,
                        "Develop": None,
                        "Delta": None,
                        "Delta %": None,
                        "Impact": "PR only",
                    }
                )
                continue

            delta = pr_display_value - develop_display_value
            delta_pct = (delta / develop_display_value * 100) if develop_display_value else None
            impact = "Regression" if delta > 0 else "Improvement" if delta < 0 else "No change"

            comparison_records.append(
                {
                    "Scenario": row["scenario"],
                    "Metric": label,
                    "Unit": unit,
                    "PR": pr_display_value,
                    "Develop": develop_display_value,
                    "Delta": delta,
                    "Delta %": delta_pct,
                    "Impact": impact,
                }
            )

    return pd.DataFrame(comparison_records)


def display_load_test_comparison(pr_data: dict[str, Any], develop_data: dict[str, Any]) -> None:
    """Display a PR load test comparison against latest develop."""
    st.subheader("PR Load Test Comparison")

    pr_run = pr_data["run"]
    develop_run = develop_data["run"]
    pr_results = pr_data["results"]
    develop_results = develop_data["results"]
    pr_sha = pr_results.get("metadata", {}).get("git_sha", pr_run["head_sha"])
    develop_sha = develop_results.get("metadata", {}).get("git_sha", develop_run["head_sha"])

    st.markdown(
        f"**PR Commit:** [{pr_sha[:7]}](https://github.com/streamlit/streamlit/commit/{pr_sha}) | "
        f"**Develop Commit:** [{develop_sha[:7]}](https://github.com/streamlit/streamlit/commit/{develop_sha})  \n"
        f"**PR Workflow Run:** [View Run]({pr_run['html_url']}) | "
        f"**Develop Workflow Run:** [View Run]({develop_run['html_url']})"
    )

    pr_summary = summarize_load_test_records(pr_data["records"])
    develop_summary = summarize_load_test_records(develop_data["records"])
    summary_metrics = [
        ("Avg initial load p50", "avg_initial_load_p50_s", "s", 2),
        ("Avg initial load p95", "avg_initial_load_p95_s", "s", 2),
        ("Avg rerun p50", "avg_rerun_p50_ms", "ms", 1),
        ("Max memory peak", "max_memory_peak_mb", "MB", 0),
        ("Failed sessions", "total_failed_sessions", "", 0),
    ]

    cols = st.columns(len(summary_metrics))
    for col, (label, key, unit, precision) in zip(cols, summary_metrics, strict=False):
        pr_value = pr_summary[key]
        delta = pr_value - develop_summary[key]
        separator = "" if not unit else " "
        with col:
            st.metric(
                label,
                f"{pr_value:.{precision}f}{separator}{unit}",
                format_metric_delta(delta, unit, precision),
                delta_color="inverse",
                border=True,
            )

    st.subheader("Scenario comparison")
    st.caption("Deltas are PR minus develop. Lower values are better for the metrics shown here.")

    comparison_df = build_scenario_comparison_df(pr_data["records"], develop_data["records"])
    if comparison_df.empty:
        st.warning("No comparable scenario metrics found.")
        return

    st.dataframe(
        comparison_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Scenario": st.column_config.TextColumn("Scenario", pinned=True),
            "Metric": st.column_config.TextColumn("Metric"),
            "Unit": st.column_config.TextColumn("Unit"),
            "PR": st.column_config.NumberColumn("PR", format="%.2f"),
            "Develop": st.column_config.NumberColumn("Develop", format="%.2f"),
            "Delta": st.column_config.NumberColumn("Delta", format="%.2f"),
            "Delta %": st.column_config.NumberColumn("Delta %", format="%.1f%%"),
            "Impact": st.column_config.TextColumn("Impact"),
        },
    )


def handle_pr_mode(pr_number: str) -> None:
    """Fetch and display load test comparison for a PR number."""
    normalized_pr_number = pr_number.strip()
    if not normalized_pr_number.isdigit():
        st.error(f"Invalid PR number: {pr_number}")
        return

    with st.spinner(f"Fetching data for PR #{normalized_pr_number}..."):
        pr_info = fetch_pr_info(normalized_pr_number)

    if not pr_info:
        st.error(f"Could not fetch information for PR #{normalized_pr_number}.")
        return

    with st.spinner("Fetching PR load test data..."):
        pr_data = get_pr_load_test(pr_info)

    with st.spinner("Fetching latest develop load test data..."):
        develop_data = get_latest_develop_load_test()

    if not pr_data or not develop_data:
        st.error("Could not fetch load test data for comparison.")
        return

    display_load_test_comparison(pr_data, develop_data)


if pr_number:
    handle_pr_mode(str(pr_number))
    st.stop()


# ── Fetch and process data ──────────────────────────────────────────────────

with st.spinner("Fetching data..."):
    workflow_runs = fetch_workflow_runs(LOAD_TESTING_WORKFLOW, limit=workflow_runs_limit, since=since_date)

    if not workflow_runs:
        st.warning("No workflow runs found for the specified criteria.")
        st.stop()

    all_records: list[dict[str, Any]] = []
    raw_results: dict[int, dict[str, Any]] = {}
    progress_bar = st.progress(0)

    for i, run in enumerate(workflow_runs):
        progress_bar.progress(
            (i + 1) / len(workflow_runs),
            text=f"Processing run {i + 1}/{len(workflow_runs)}: {run['head_sha'][:7]}",
        )

        results = get_load_test_results(run["id"])
        if results:
            all_records.extend(flatten_scenario_records(run, results))
            raw_results[run["id"]] = results

    progress_bar.empty()

    if not all_records:
        st.warning("No load test results found in the workflow runs.")
        st.stop()

    df = pd.DataFrame(all_records)
    df = df.sort_values("created_at")

scenarios = sorted(df["scenario"].unique())

# ── Latest-run KPI metrics ──────────────────────────────────────────────────

latest_date = df["created_at"].max()
latest_df = df[df["created_at"] == latest_date]

st.subheader("Latest run overview")
st.caption(
    f"Commit [{latest_df.iloc[0]['commit_sha']}]({latest_df.iloc[0]['commit_url']}) "
    f"· {latest_df.iloc[0]['concurrent_users']} concurrent users "
    f"· {latest_df.iloc[0]['runner']}"
)

for _, row in latest_df.iterrows():
    scenario_history = df[df["scenario"] == row["scenario"]].tail(20)
    with st.container(border=True):
        st.markdown(f"**{row['scenario']}**")
        cols = st.columns(6)
        cols[0].metric(
            "Initial load (p50)",
            f"{row['initial_load_p50_ms'] / 1000:.1f}s",
            border=True,
            chart_data=scenario_history["initial_load_p50_ms"] / 1000,
            chart_type="line",
        )
        cols[1].metric(
            "Initial load (p95)",
            f"{row['initial_load_p95_ms'] / 1000:.1f}s",
            border=True,
            chart_data=scenario_history["initial_load_p95_ms"] / 1000,
            chart_type="line",
        )
        cols[2].metric(
            "Rerun (p50)",
            f"{row['rerun_p50_ms']:.0f} ms",
            border=True,
            chart_data=scenario_history["rerun_p50_ms"],
            chart_type="line",
        )
        cols[3].metric(
            "Rerun (p95)",
            f"{row['rerun_p95_ms']:.0f} ms",
            border=True,
            chart_data=scenario_history["rerun_p95_ms"],
            chart_type="line",
        )
        cols[4].metric(
            "Memory peak",
            f"{row['memory_peak_mb']:.0f} MB",
            border=True,
            chart_data=scenario_history["memory_peak_mb"],
            chart_type="line",
        )
        cols[5].metric(
            "Failed sessions",
            int(row["sessions_failed"]),
            border=True,
            chart_data=scenario_history["sessions_failed"],
            chart_type="bar",
        )


# ── Scenario filter ─────────────────────────────────────────────────────────

st.divider()
selected_scenarios = st.sidebar.multiselect(
    "Scenarios",
    options=scenarios,
    default=scenarios,
    help="Filter the charts below to specific scenarios.",
)

filtered_df = df[df["scenario"].isin(selected_scenarios)]

# ── Initial load time over time ─────────────────────────────────────────────

st.subheader("Initial load time over time")

tab_p50, tab_p95, tab_p99 = st.tabs(["p50", "p95", "p99"])

for tab, metric_col, label in [
    (tab_p50, "initial_load_p50_ms", "p50"),
    (tab_p95, "initial_load_p95_ms", "p95"),
    (tab_p99, "initial_load_p99_ms", "p99"),
]:
    with tab:
        chart_df = filtered_df.copy()
        chart_df["value_s"] = chart_df[metric_col] / 1000
        fig = px.line(
            chart_df,
            x="created_at",
            y="value_s",
            color="scenario",
            labels={
                "created_at": "Date",
                "value_s": f"Initial load {label} (s)",
                "scenario": "Scenario",
            },
            markers=True,
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title=f"Initial load {label} (seconds)",
            hovermode="closest",
        )
        fig.update_traces(
            hovertemplate=("<b>Date:</b> %{x|%Y-%m-%d}<br><b>Commit:</b> %{customdata[0]}<br><b>Value:</b> %{y:.2f}s"),
            customdata=chart_df[["commit_sha"]],
        )
        st.plotly_chart(fig, width="stretch")

# ── Rerun time over time ────────────────────────────────────────────────────

st.subheader("Rerun time over time")

tab_p50, tab_p95, tab_p99 = st.tabs(["p50", "p95", "p99"])

for tab, metric_col, label in [
    (tab_p50, "rerun_p50_ms", "p50"),
    (tab_p95, "rerun_p95_ms", "p95"),
    (tab_p99, "rerun_p99_ms", "p99"),
]:
    with tab:
        chart_df = filtered_df.copy()
        fig = px.line(
            chart_df,
            x="created_at",
            y=metric_col,
            color="scenario",
            labels={
                "created_at": "Date",
                metric_col: f"Rerun {label} (ms)",
                "scenario": "Scenario",
            },
            markers=True,
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title=f"Rerun {label} (ms)",
            hovermode="closest",
        )
        fig.update_traces(
            hovertemplate=(
                "<b>Date:</b> %{x|%Y-%m-%d}<br><b>Commit:</b> %{customdata[0]}<br><b>Value:</b> %{y:.1f} ms"
            ),
            customdata=chart_df[["commit_sha"]],
        )
        st.plotly_chart(fig, width="stretch")

# ── Memory usage over time ──────────────────────────────────────────────────

st.subheader("Memory usage over time")

tab_peak, tab_growth, tab_avg = st.tabs(["Peak RSS", "RSS growth", "Average RSS"])

for tab, metric_col, label in [
    (tab_peak, "memory_peak_mb", "Peak RSS (MB)"),
    (tab_growth, "memory_growth_mb", "RSS growth (MB)"),
    (tab_avg, "memory_avg_mb", "Average RSS (MB)"),
]:
    with tab:
        fig = px.line(
            filtered_df,
            x="created_at",
            y=metric_col,
            color="scenario",
            labels={
                "created_at": "Date",
                metric_col: label,
                "scenario": "Scenario",
            },
            markers=True,
        )
        fig.update_layout(xaxis_title="Date", yaxis_title=label, hovermode="closest")
        fig.update_traces(
            hovertemplate=(
                "<b>Date:</b> %{x|%Y-%m-%d}<br><b>Commit:</b> %{customdata[0]}<br><b>Value:</b> %{y:.1f} MB"
            ),
            customdata=filtered_df[["commit_sha"]],
        )
        st.plotly_chart(fig, width="stretch")

# ── CPU usage over time ─────────────────────────────────────────────────────

st.subheader("CPU usage over time")

tab_avg_cpu, tab_peak_cpu = st.tabs(["Average CPU %", "Peak CPU %"])

for tab, metric_col, label in [
    (tab_avg_cpu, "cpu_avg_pct", "Average CPU (%)"),
    (tab_peak_cpu, "cpu_peak_pct", "Peak CPU (%)"),
]:
    with tab:
        fig = px.line(
            filtered_df,
            x="created_at",
            y=metric_col,
            color="scenario",
            labels={
                "created_at": "Date",
                metric_col: label,
                "scenario": "Scenario",
            },
            markers=True,
        )
        fig.update_layout(xaxis_title="Date", yaxis_title=label, hovermode="closest")
        fig.update_traces(
            hovertemplate=("<b>Date:</b> %{x|%Y-%m-%d}<br><b>Commit:</b> %{customdata[0]}<br><b>Value:</b> %{y:.1f}%"),
            customdata=filtered_df[["commit_sha"]],
        )
        st.plotly_chart(fig, width="stretch")

# ── Test duration over time ─────────────────────────────────────────────────

st.subheader("Scenario duration over time")

fig_duration = px.line(
    filtered_df,
    x="created_at",
    y="duration_seconds",
    color="scenario",
    labels={
        "created_at": "Date",
        "duration_seconds": "Duration (s)",
        "scenario": "Scenario",
    },
    markers=True,
)
fig_duration.update_layout(xaxis_title="Date", yaxis_title="Duration (seconds)", hovermode="closest")
fig_duration.update_traces(
    hovertemplate=("<b>Date:</b> %{x|%Y-%m-%d}<br><b>Commit:</b> %{customdata[0]}<br><b>Duration:</b> %{y:.1f}s"),
    customdata=filtered_df[["commit_sha"]],
)
st.plotly_chart(fig_duration, width="stretch")

# ── Run history table ────────────────────────────────────────────────────────

st.subheader("Run history")
st.caption(":material/keyboard_arrow_down: Select a row to view detailed results for that run.")

run_summary_records = []
for run_id, results in raw_results.items():
    metadata = results.get("metadata", {})
    scenario_list = results.get("scenarios", [])
    if not scenario_list:
        continue

    avg_initial_load_p50 = sum(
        s.get("session_metrics", {}).get("initial_load_time_ms", {}).get("p50", 0) for s in scenario_list
    ) / len(scenario_list)

    avg_rerun_p50 = sum(
        s.get("session_metrics", {}).get("rerun_time_ms", {}).get("p50", 0) for s in scenario_list
    ) / len(scenario_list)

    max_memory_peak = max(s.get("server_metrics", {}).get("memory_rss_mb_peak", 0) for s in scenario_list)

    total_failed = sum(s.get("session_metrics", {}).get("sessions_failed", 0) for s in scenario_list)

    matching_runs = [r for r in workflow_runs if r["id"] == run_id]
    run_info = matching_runs[0] if matching_runs else {}
    git_sha = metadata.get("git_sha", run_info.get("head_sha", ""))

    run_summary_records.append(
        {
            "run_id": run_id,
            "created_at": datetime.strptime(run_info["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            if run_info.get("created_at")
            else None,
            "commit_sha": git_sha[:7],
            "commit_url": f"https://github.com/streamlit/streamlit/commit/{git_sha}",
            "run_url": run_info.get("html_url", ""),
            "scenarios": len(scenario_list),
            "concurrent_users": scenario_list[0].get("concurrent_users", 0),
            "avg_initial_load_p50_s": avg_initial_load_p50 / 1000,
            "avg_rerun_p50_ms": avg_rerun_p50,
            "max_memory_peak_mb": max_memory_peak,
            "total_failed_sessions": total_failed,
        }
    )

if run_summary_records:
    history_df = pd.DataFrame(run_summary_records).sort_values("created_at", ascending=False)

    df_selection = st.dataframe(
        history_df,
        width="stretch",
        column_config={
            "created_at": st.column_config.DatetimeColumn("Date", format="distance"),
            "commit_sha": st.column_config.TextColumn("Commit"),
            "scenarios": st.column_config.NumberColumn("Scenarios"),
            "concurrent_users": st.column_config.NumberColumn("Users"),
            "avg_initial_load_p50_s": st.column_config.NumberColumn("Avg initial load p50 (s)", format="%.2f"),
            "avg_rerun_p50_ms": st.column_config.NumberColumn("Avg rerun p50 (ms)", format="%.1f"),
            "max_memory_peak_mb": st.column_config.NumberColumn("Max memory peak (MB)", format="%.0f"),
            "total_failed_sessions": st.column_config.NumberColumn("Failed sessions"),
            "run_url": st.column_config.LinkColumn("Workflow Run", display_text="View Run"),
            "commit_url": st.column_config.LinkColumn(
                "Commit",
                display_text="https://github.com/streamlit/streamlit/commit/([a-f0-9]{7}).*",
            ),
        },
        hide_index=True,
        column_order=[
            "created_at",
            "scenarios",
            "concurrent_users",
            "avg_initial_load_p50_s",
            "avg_rerun_p50_ms",
            "max_memory_peak_mb",
            "total_failed_sessions",
            "commit_url",
            "run_url",
        ],
        on_select="rerun",
        selection_mode="single-row",
        key="run_history_df",
    )

    # ── Detail view for a selected run ──────────────────────────────────────

    def display_run_details(results: dict[str, Any]) -> None:
        """Render detailed results for a single load test run."""
        metadata = results.get("metadata", {})
        scenario_list = results.get("scenarios", [])

        st.header(f"Details for commit {metadata.get('git_sha', '')[:7]}")

        cols = st.columns(3)
        cols[0].metric("Git branch", metadata.get("git_branch", "N/A"), border=True)
        cols[1].metric("Runner", metadata.get("runner", "N/A"), border=True)
        cols[2].metric("Scenarios", len(scenario_list), border=True)

        for scenario in scenario_list:
            server = scenario.get("server_metrics", {})
            session = scenario.get("session_metrics", {})
            initial_load = session.get("initial_load_time_ms", {})
            rerun = session.get("rerun_time_ms", {})

            st.subheader(scenario.get("scenario", "unknown"))

            cols = st.columns(4)
            cols[0].metric(
                "Concurrent users",
                scenario.get("concurrent_users", 0),
                border=True,
            )
            cols[1].metric(
                "Duration",
                f"{scenario.get('duration_seconds', 0):.1f}s",
                border=True,
            )
            cols[2].metric(
                "Sessions completed",
                f"{session.get('sessions_completed', 0)}/{session.get('total_sessions', 0)}",
                border=True,
            )
            cols[3].metric(
                "Failed",
                session.get("sessions_failed", 0),
                border=True,
            )

            tab_timing, tab_server = st.tabs(["Session timing", "Server metrics"])

            with tab_timing:
                timing_data = {
                    "Metric": [
                        "Initial load",
                        "Rerun",
                    ],
                    "Min (ms)": [
                        initial_load.get("min", 0),
                        rerun.get("min", 0),
                    ],
                    "Mean (ms)": [
                        initial_load.get("mean", 0),
                        rerun.get("mean", 0),
                    ],
                    "p50 (ms)": [
                        initial_load.get("p50", 0),
                        rerun.get("p50", 0),
                    ],
                    "p95 (ms)": [
                        initial_load.get("p95", 0),
                        rerun.get("p95", 0),
                    ],
                    "p99 (ms)": [
                        initial_load.get("p99", 0),
                        rerun.get("p99", 0),
                    ],
                    "Max (ms)": [
                        initial_load.get("max", 0),
                        rerun.get("max", 0),
                    ],
                }
                timing_df = pd.DataFrame(timing_data)
                st.dataframe(
                    timing_df,
                    column_config={
                        "Metric": st.column_config.TextColumn("Metric", pinned=True),
                        "Min (ms)": st.column_config.NumberColumn(format="%.1f"),
                        "Mean (ms)": st.column_config.NumberColumn(format="%.1f"),
                        "p50 (ms)": st.column_config.NumberColumn(format="%.1f"),
                        "p95 (ms)": st.column_config.NumberColumn(format="%.1f"),
                        "p99 (ms)": st.column_config.NumberColumn(format="%.1f"),
                        "Max (ms)": st.column_config.NumberColumn(format="%.1f"),
                    },
                    hide_index=True,
                    width="stretch",
                )

            with tab_server:
                server_cols = st.columns(3)
                server_cols[0].metric(
                    "Memory peak",
                    f"{server.get('memory_rss_mb_peak', 0):.1f} MB",
                    border=True,
                )
                server_cols[1].metric(
                    "Memory growth",
                    f"{server.get('memory_rss_mb_growth', 0):.1f} MB",
                    border=True,
                )
                server_cols[2].metric(
                    "Memory avg",
                    f"{server.get('memory_rss_mb_avg', 0):.1f} MB",
                    border=True,
                )

                server_cols = st.columns(3)
                server_cols[0].metric(
                    "CPU avg",
                    f"{server.get('cpu_percent_avg', 0):.1f}%",
                    border=True,
                )
                server_cols[1].metric(
                    "CPU peak",
                    f"{server.get('cpu_percent_peak', 0):.1f}%",
                    border=True,
                )
                server_cols[2].metric(
                    "Max threads",
                    server.get("thread_count_max", 0),
                    border=True,
                )

            errors = session.get("errors", [])
            if errors:
                st.error(f"{len(errors)} error(s) recorded")
                for err in errors:
                    st.code(str(err))

    if df_selection["selection"]["rows"]:
        selected_idx = df_selection["selection"]["rows"][0]
        selected_row = history_df.iloc[selected_idx]
        selected_run_id = selected_row["run_id"]

        if selected_run_id in raw_results:
            display_run_details(raw_results[selected_run_id])
        else:
            st.warning("Results data not available for this run.")
    else:
        st.info("Select a row from the table above to view detailed results for that run.")
