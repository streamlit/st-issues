from __future__ import annotations

import json
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any
from zipfile import ZipFile

import pandas as pd
import plotly.express as px
import streamlit as st

from app.utils.github_utils import (
    download_artifact,
    fetch_artifacts,
    fetch_workflow_runs,
)

st.set_page_config(page_title="Playwright test stats", page_icon="🎭", layout="wide")

title_row = st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center")
with title_row:
    st.title("🎭 Playwright test stats")
    if st.button(":material/refresh: Refresh Data", type="tertiary"):
        fetch_workflow_runs.clear()

st.caption(
    "This page visualizes Playwright end-to-end test statistics over time, "
    "based on the `playwright.yml` workflow runs on the develop branch."
)

# Sidebar controls
time_period = st.sidebar.selectbox(
    "Time period",
    options=["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
    help="The time period to display test stats for. "
    "But it will still only load the last X workflow runs as defined by the slider below.",
    index=3,
)
workflow_runs_limit = st.sidebar.slider(
    "Number of workflow runs",
    min_value=50,
    max_value=250,
    value=50,
    step=50,
    help="This is equivalent to the number of commits to develop to include in the analysis.",
)

since_date: datetime | None
if time_period == "Last 7 days":
    since_date = datetime.now() - timedelta(days=7)
elif time_period == "Last 30 days":
    since_date = datetime.now() - timedelta(days=30)
elif time_period == "Last 90 days":
    since_date = datetime.now() - timedelta(days=90)
else:
    since_date = None


@st.cache_data(show_spinner=False)
def get_test_stats_from_artifact(run_id: int) -> dict[str, Any] | None:
    """Download and parse the test-stats.json from a playwright workflow run."""
    artifacts = fetch_artifacts(run_id)

    stats_artifact = None
    for artifact in artifacts:
        if artifact["name"].startswith("playwright_test_stats"):
            stats_artifact = artifact
            break

    if not stats_artifact:
        return None

    artifact_content = download_artifact(stats_artifact["archive_download_url"])
    if not artifact_content:
        return None

    try:
        with ZipFile(BytesIO(artifact_content)) as zip_file:
            for name in zip_file.namelist():
                if name.endswith(".json"):
                    with zip_file.open(name) as f:
                        return json.load(f)
    except Exception:
        return None
    return None


def extract_summary_record(run: dict[str, Any], stats: dict[str, Any]) -> dict[str, Any]:
    """Build a flat record from a workflow run and its test-stats.json."""
    summary = stats.get("summary", {})
    duration = stats.get("duration", {})
    browser = stats.get("browser_breakdown", {})
    memory = stats.get("memory", {})
    xdist = stats.get("xdist_workers", {})
    aggregate = xdist.get("aggregate", {})

    return {
        "run_id": run["id"],
        "created_at": datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
        "commit_sha": run["head_sha"][:7],
        "commit_url": f"https://github.com/streamlit/streamlit/commit/{run['head_sha']}",
        "run_url": run["html_url"],
        # Summary
        "total_tests": summary.get("total_tests", 0),
        "passed": summary.get("passed", 0),
        "failed": summary.get("failed", 0),
        "skipped": summary.get("skipped", 0),
        "errors": summary.get("errors", 0),
        "tests_with_reruns": summary.get("tests_with_reruns", 0),
        "total_reruns": summary.get("total_reruns", 0),
        # Duration
        "session_duration_s": duration.get("session_duration_seconds", 0),
        "total_test_time_s": duration.get("total_test_time_seconds", 0),
        "mean_duration_s": duration.get("mean_duration_seconds", 0),
        "median_duration_s": duration.get("median_duration_seconds", 0),
        "max_duration_s": duration.get("max_duration_seconds", 0),
        "mean_setup_s": duration.get("mean_setup_duration_seconds", 0),
        "mean_teardown_s": duration.get("mean_teardown_duration_seconds", 0),
        # Browser totals
        "chromium_total": browser.get("chromium", {}).get("total", 0),
        "firefox_total": browser.get("firefox", {}).get("total", 0),
        "webkit_total": browser.get("webkit", {}).get("total", 0),
        "chromium_failed": browser.get("chromium", {}).get("failed", 0),
        "firefox_failed": browser.get("firefox", {}).get("failed", 0),
        "webkit_failed": browser.get("webkit", {}).get("failed", 0),
        # Workers
        "worker_count": xdist.get("worker_count", 0),
        "avg_worker_runtime_s": aggregate.get("avg_runtime_seconds", 0),
        "max_worker_runtime_s": aggregate.get("max_runtime_seconds", 0),
        # Memory
        "total_memory_mb": memory.get("total_rss_mb", 0),
        "workers_memory_mb": memory.get("workers_rss_mb", 0),
    }


# ── Fetch and process data ──────────────────────────────────────────────────

with st.spinner("Fetching data..."):
    workflow_runs = fetch_workflow_runs("playwright.yml", limit=workflow_runs_limit, since=since_date)

    if not workflow_runs:
        st.warning("No workflow runs found for the specified criteria.")
        st.stop()

    records: list[dict[str, Any]] = []
    raw_stats: dict[int, dict[str, Any]] = {}
    progress_bar = st.progress(0)

    for i, run in enumerate(workflow_runs):
        progress_bar.progress(
            (i + 1) / len(workflow_runs),
            text=f"Processing run {i + 1}/{len(workflow_runs)}: {run['head_sha'][:7]}",
        )

        stats = get_test_stats_from_artifact(run["id"])
        if stats:
            records.append(extract_summary_record(run, stats))
            raw_stats[run["id"]] = stats

    progress_bar.empty()

    if not records:
        st.warning("No Playwright test stats artifacts found in the workflow runs.")
        st.stop()

    df = pd.DataFrame(records)
    df = df.sort_values("created_at")

# ── Top-level metrics ────────────────────────────────────────────────────────

latest = df.iloc[-1]
oldest = df.iloc[0]

tests_delta = int(latest["total_tests"] - oldest["total_tests"])
session_delta = latest["session_duration_s"] - oldest["session_duration_s"]
reruns_latest = int(latest["total_reruns"])

sparkline_data = df.tail(20)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Tests",
        f"{int(latest['total_tests']):,}",
        delta=f"{tests_delta:+,}",
        delta_color="off",
        border=True,
        chart_data=sparkline_data["total_tests"],
        chart_type="line",
    )
with col2:
    st.metric(
        "Session Duration",
        f"{latest['session_duration_s'] / 60:.1f} min",
        delta=f"{session_delta / 60:+.1f} min",
        delta_color="inverse",
        border=True,
        chart_data=sparkline_data["session_duration_s"],
        chart_type="line",
    )
with col3:
    st.metric(
        "Reruns (latest)",
        reruns_latest,
        border=True,
        chart_data=sparkline_data["total_reruns"],
        chart_type="line",
    )

mean_delta = latest["mean_duration_s"] - oldest["mean_duration_s"]
median_delta = latest["median_duration_s"] - oldest["median_duration_s"]
memory_delta = latest["total_memory_mb"] - oldest["total_memory_mb"]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Mean Test Duration",
        f"{latest['mean_duration_s']:.2f}s",
        delta=f"{mean_delta:+.2f}s",
        delta_color="inverse",
        border=True,
        chart_data=sparkline_data["mean_duration_s"],
        chart_type="line",
    )
with col2:
    st.metric(
        "Median Test Duration",
        f"{latest['median_duration_s']:.2f}s",
        delta=f"{median_delta:+.2f}s",
        delta_color="inverse",
        border=True,
        chart_data=sparkline_data["median_duration_s"],
        chart_type="line",
    )
with col3:
    st.metric(
        "Total Memory",
        f"{latest['total_memory_mb'] / 1024:.1f} GB",
        delta=f"{memory_delta / 1024:+.1f} GB",
        delta_color="inverse",
        border=True,
        chart_data=sparkline_data["total_memory_mb"],
        chart_type="line",
    )

# ── Total tests over time ───────────────────────────────────────────────────

st.subheader("Total Tests Over Time")

fig_tests = px.line(
    df,
    x="created_at",
    y="total_tests",
    labels={"created_at": "Date", "total_tests": "Total Tests"},
    markers=True,
)
fig_tests.update_traces(
    hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Commit:</b> %{customdata[0]}<br><b>Total Tests:</b> %{y:,}",
    customdata=df[["commit_sha"]],
)
fig_tests.update_layout(xaxis_title="Date", yaxis_title="Total Tests", hovermode="closest")
st.plotly_chart(fig_tests, width="stretch")

# ── Browser breakdown over time ──────────────────────────────────────────────

st.subheader("Tests by Browser Over Time")

df_browser = pd.melt(
    df,
    id_vars=["created_at", "commit_sha"],
    value_vars=["chromium_total", "firefox_total", "webkit_total"],
    var_name="Browser",
    value_name="Test Count",
)
df_browser["Browser"] = df_browser["Browser"].map(
    {
        "chromium_total": "Chromium",
        "firefox_total": "Firefox",
        "webkit_total": "WebKit",
    }
)

fig_browser = px.line(
    df_browser,
    x="created_at",
    y="Test Count",
    color="Browser",
    labels={"created_at": "Date"},
    markers=True,
)
fig_browser.update_layout(xaxis_title="Date", yaxis_title="Test Count", hovermode="closest")
st.plotly_chart(fig_browser, width="stretch")

# ── Duration trends ──────────────────────────────────────────────────────────

st.subheader("Duration Trends")

tab_session, tab_test_durations = st.tabs(["Session Duration", "Test Durations"])

with tab_session:
    df["session_duration_min"] = df["session_duration_s"] / 60
    fig_session = px.line(
        df,
        x="created_at",
        y="session_duration_min",
        labels={"created_at": "Date", "session_duration_min": "Session Duration (min)"},
        markers=True,
    )
    fig_session.update_traces(
        hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Commit:</b> %{customdata[0]}<br><b>Duration:</b> %{y:.1f} min",
        customdata=df[["commit_sha"]],
    )
    fig_session.update_layout(xaxis_title="Date", yaxis_title="Duration (min)", hovermode="closest")
    st.plotly_chart(fig_session, width="stretch")

with tab_test_durations:
    df_durations = pd.melt(
        df,
        id_vars=["created_at", "commit_sha"],
        value_vars=["mean_duration_s", "median_duration_s", "max_duration_s"],
        var_name="Metric",
        value_name="Duration (s)",
    )
    df_durations["Metric"] = df_durations["Metric"].map(
        {
            "mean_duration_s": "Mean",
            "median_duration_s": "Median",
            "max_duration_s": "Max",
        }
    )

    fig_durations = px.line(
        df_durations,
        x="created_at",
        y="Duration (s)",
        color="Metric",
        labels={"created_at": "Date"},
        markers=True,
    )
    fig_durations.update_layout(xaxis_title="Date", yaxis_title="Duration (seconds)", hovermode="closest")
    st.plotly_chart(fig_durations, width="stretch")

# ── Failures & reruns over time ──────────────────────────────────────────────

st.subheader("Failures & Reruns Over Time")

df_failures = pd.melt(
    df,
    id_vars=["created_at", "commit_sha"],
    value_vars=["failed", "errors", "total_reruns"],
    var_name="Metric",
    value_name="Count",
)
df_failures["Metric"] = df_failures["Metric"].map(
    {
        "failed": "Failed",
        "errors": "Errors",
        "total_reruns": "Reruns",
    }
)

fig_failures = px.line(
    df_failures,
    x="created_at",
    y="Count",
    color="Metric",
    labels={"created_at": "Date"},
    markers=True,
)
fig_failures.update_layout(xaxis_title="Date", yaxis_title="Count", hovermode="closest")
st.plotly_chart(fig_failures, width="stretch")

# ── Memory usage over time ───────────────────────────────────────────────────

st.subheader("Memory Usage Over Time")

df["workers_memory_gb"] = df["workers_memory_mb"] / 1024
df["total_memory_gb"] = df["total_memory_mb"] / 1024

df_memory = pd.melt(
    df,
    id_vars=["created_at", "commit_sha"],
    value_vars=["workers_memory_gb", "total_memory_gb"],
    var_name="Metric",
    value_name="Memory (GB)",
)
df_memory["Metric"] = df_memory["Metric"].map(
    {
        "workers_memory_gb": "Workers",
        "total_memory_gb": "Total (incl. main process)",
    }
)

fig_memory = px.line(
    df_memory,
    x="created_at",
    y="Memory (GB)",
    color="Metric",
    labels={"created_at": "Date"},
    markers=True,
)
fig_memory.update_layout(xaxis_title="Date", yaxis_title="Memory (GB)", hovermode="closest")
st.plotly_chart(fig_memory, width="stretch")

# ── Run history table ────────────────────────────────────────────────────────

st.subheader("Run History")

st.caption(":material/keyboard_arrow_down: Select a row to view detailed stats for that run.")

history_df = df.sort_values("created_at", ascending=False).copy()
history_df["session_duration_min"] = history_df["session_duration_s"] / 60

df_selection = st.dataframe(
    history_df,
    width="stretch",
    column_config={
        "created_at": st.column_config.DatetimeColumn("Date", format="distance"),
        "commit_sha": st.column_config.TextColumn("Commit"),
        "total_tests": st.column_config.NumberColumn("Total Tests"),
        "passed": st.column_config.NumberColumn("Passed"),
        "failed": st.column_config.NumberColumn("Failed"),
        "total_reruns": st.column_config.NumberColumn("Reruns"),
        "session_duration_min": st.column_config.NumberColumn("Session (min)", format="%.1f"),
        "mean_duration_s": st.column_config.NumberColumn("Mean Duration (s)", format="%.2f"),
        "total_memory_mb": st.column_config.NumberColumn("Memory (MB)", format="%.0f"),
        "run_url": st.column_config.LinkColumn("Workflow Run", display_text="View Run"),
        "commit_url": st.column_config.LinkColumn(
            "Commit",
            display_text="https://github.com/streamlit/streamlit/commit/([a-f0-9]{7}).*",
        ),
    },
    hide_index=True,
    column_order=[
        "created_at",
        "total_tests",
        "passed",
        "failed",
        "total_reruns",
        "session_duration_min",
        "mean_duration_s",
        "total_memory_mb",
        "commit_url",
        "run_url",
    ],
    on_select="rerun",
    selection_mode="single-row",
    key="run_history_df",
)


# ── Detail view for a selected run ───────────────────────────────────────────


def display_run_details(stats: dict[str, Any], run_record: pd.Series) -> None:
    """Render detailed stats for a single Playwright run."""
    summary = stats.get("summary", {})
    duration = stats.get("duration", {})
    browser = stats.get("browser_breakdown", {})
    xdist = stats.get("xdist_workers", {})
    memory = stats.get("memory", {})

    st.header(f"Details for commit {run_record['commit_sha']}")

    # ── Summary metrics ──────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tests", f"{summary.get('total_tests', 0):,}", border=True)
    col2.metric("Passed", f"{summary.get('passed', 0):,}", border=True)
    col3.metric("Failed", summary.get("failed", 0), border=True)
    col4.metric("Skipped", summary.get("skipped", 0), border=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Session Duration",
        f"{duration.get('session_duration_seconds', 0) / 60:.1f} min",
        border=True,
    )
    col2.metric(
        "Total Test Time",
        f"{duration.get('total_test_time_seconds', 0) / 60:.1f} min",
        border=True,
    )
    col3.metric(
        "Mean Duration",
        f"{duration.get('mean_duration_seconds', 0):.2f}s",
        border=True,
    )
    col4.metric(
        "Median Duration",
        f"{duration.get('median_duration_seconds', 0):.2f}s",
        border=True,
    )

    # ── Browser breakdown ────────────────────────────────────────────────
    st.subheader("Browser Breakdown")

    browser_rows = []
    for name, data in browser.items():
        browser_rows.append(
            {
                "Browser": name.capitalize(),
                "Total": data.get("total", 0),
                "Passed": data.get("passed", 0),
                "Failed": data.get("failed", 0),
                "Skipped": data.get("skipped", 0),
                "Errors": data.get("errors", 0),
            }
        )

    if browser_rows:
        browser_df = pd.DataFrame(browser_rows)

        col1, col2 = st.columns(2)
        with col1:
            fig_pie = px.pie(
                browser_df,
                names="Browser",
                values="Total",
                title="Test Distribution by Browser",
                color="Browser",
                color_discrete_map={
                    "Chromium": "#4285F4",
                    "Firefox": "#FF7139",
                    "Webkit": "#006CFF",
                },
            )
            st.plotly_chart(fig_pie, width="stretch")

        with col2:
            st.dataframe(
                browser_df,
                hide_index=True,
                width="stretch",
            )

    # ── Slowest tests ────────────────────────────────────────────────────
    slowest_tests = stats.get("slowest_tests", [])
    if slowest_tests:
        st.subheader("Top 10 Slowest Tests")

        slowest_df = pd.DataFrame(slowest_tests)
        slowest_df["total_s"] = (
            slowest_df["duration_seconds"]
            + slowest_df["setup_duration_seconds"]
            + slowest_df["teardown_duration_seconds"]
        )

        fig_slow = px.bar(
            slowest_df,
            y="nodeid",
            x=["setup_duration_seconds", "duration_seconds", "teardown_duration_seconds"],
            orientation="h",
            labels={"value": "Duration (s)", "nodeid": "Test"},
            title="Slowest Tests (setup + test + teardown)",
            color_discrete_map={
                "setup_duration_seconds": "#636EFA",
                "duration_seconds": "#EF553B",
                "teardown_duration_seconds": "#00CC96",
            },
        )
        fig_slow.update_layout(
            yaxis={"categoryorder": "total ascending"},
            legend_title_text="Phase",
            barmode="stack",
            height=max(400, len(slowest_df) * 40),
        )
        for trace in fig_slow.data:
            trace.name = (
                trace.name.replace("_duration_seconds", "")
                .replace("_seconds", "")
                .replace("duration", "test")
                .capitalize()
            )
        st.plotly_chart(fig_slow, width="stretch")

    # ── Slowest modules ──────────────────────────────────────────────────
    test_modules = stats.get("test_modules", [])
    if test_modules:
        st.subheader("Test Modules by Total Duration")

        modules_df = pd.DataFrame(test_modules)
        modules_df = modules_df.sort_values("total_duration_seconds", ascending=False)

        top_n = min(25, len(modules_df))
        top_modules = modules_df.head(top_n)

        fig_modules = px.bar(
            top_modules,
            y="module",
            x="total_duration_seconds",
            orientation="h",
            color="avg_duration_seconds",
            color_continuous_scale="RdYlGn_r",
            labels={
                "total_duration_seconds": "Total Duration (s)",
                "module": "Module",
                "avg_duration_seconds": "Avg Duration (s)",
            },
            hover_data=["test_count", "avg_duration_seconds"],
            title=f"Top {top_n} Modules by Total Duration",
        )
        fig_modules.update_layout(
            yaxis={"categoryorder": "total ascending"},
            height=max(500, top_n * 28),
        )
        st.plotly_chart(fig_modules, width="stretch")

        st.caption("Full module list")
        st.dataframe(
            modules_df,
            column_config={
                "module": st.column_config.TextColumn("Module"),
                "total_duration_seconds": st.column_config.NumberColumn("Total Duration (s)", format="%.1f"),
                "test_count": st.column_config.NumberColumn("Tests"),
                "avg_duration_seconds": st.column_config.NumberColumn("Avg Duration (s)", format="%.2f"),
            },
            hide_index=True,
            width="stretch",
        )

    # ── xdist worker distribution ────────────────────────────────────────
    per_worker = xdist.get("per_worker", {})
    if per_worker:
        st.subheader("xdist Worker Distribution")

        worker_rows = []
        for worker_name, worker_data in sorted(per_worker.items()):
            worker_rows.append(
                {
                    "Worker": worker_name,
                    "Tests": worker_data.get("test_count", 0),
                    "Runtime (s)": worker_data.get("total_runtime_seconds", 0),
                    "Avg Duration (s)": worker_data.get("avg_test_duration_seconds", 0),
                    "Memory (MB)": worker_data.get("memory_mb", 0),
                }
            )

        worker_df = pd.DataFrame(worker_rows)

        col1, col2 = st.columns(2)
        with col1:
            fig_worker_tests = px.bar(
                worker_df,
                x="Worker",
                y="Tests",
                color="Runtime (s)",
                color_continuous_scale="Blues",
                title="Tests per Worker",
            )
            fig_worker_tests.update_layout(height=400)
            st.plotly_chart(fig_worker_tests, width="stretch")

        with col2:
            fig_worker_mem = px.bar(
                worker_df,
                x="Worker",
                y="Memory (MB)",
                color="Memory (MB)",
                color_continuous_scale="Reds",
                title="Memory per Worker",
            )
            fig_worker_mem.update_layout(height=400)
            st.plotly_chart(fig_worker_mem, width="stretch")

        aggregate = xdist.get("aggregate", {})
        if aggregate:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(
                "Avg Tests/Worker",
                f"{aggregate.get('avg_tests_per_worker', 0):.0f}",
                border=True,
            )
            col2.metric(
                "Avg Runtime/Worker",
                f"{aggregate.get('avg_runtime_seconds', 0) / 60:.1f} min",
                border=True,
            )
            col3.metric(
                "Max Runtime (Worker)",
                f"{aggregate.get('max_runtime_seconds', 0) / 60:.1f} min",
                border=True,
            )
            col4.metric(
                "Avg Memory/Worker",
                f"{aggregate.get('avg_memory_mb', 0):.0f} MB",
                border=True,
            )

    # ── Rerun details ────────────────────────────────────────────────────
    rerun_details = stats.get("rerun_details", [])
    if rerun_details:
        st.subheader("Rerun Details")
        rerun_df = pd.DataFrame(rerun_details)
        st.dataframe(
            rerun_df,
            column_config={
                "nodeid": st.column_config.TextColumn("Test"),
                "final_outcome": st.column_config.TextColumn("Final Outcome"),
                "rerun_count": st.column_config.NumberColumn("Rerun Count"),
                "browser": st.column_config.TextColumn("Browser"),
            },
            hide_index=True,
            width="stretch",
        )

    # ── Environment info ─────────────────────────────────────────────────
    env = stats.get("environment", {})
    if env:
        st.subheader("Environment")
        env_cols = st.columns(4)
        env_cols[0].metric("Python Version", env.get("python_version", "N/A").split(" ")[0], border=True)
        env_cols[1].metric("Platform", env.get("platform", "N/A"), border=True)
        env_cols[2].metric("Pytest Version", env.get("pytest_version", "N/A"), border=True)
        env_cols[3].metric(
            "Memory (Total)",
            f"{memory.get('total_rss_mb', 0) / 1024:.1f} GB",
            border=True,
        )


if df_selection["selection"]["rows"]:
    selected_idx = df_selection["selection"]["rows"][0]
    selected_row = history_df.iloc[selected_idx]
    selected_run_id = selected_row["run_id"]

    if selected_run_id in raw_stats:
        display_run_details(raw_stats[selected_run_id], selected_row)
    else:
        st.warning("Stats data not available for this run.")
else:
    st.info("Select a row from the table above to view detailed stats for that run.")
