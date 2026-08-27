from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from app.utils.ai_workflow_runs import (
    OUTCOME_CANCELLED,
    OUTCOME_FAILED,
    OUTCOME_SUCCEEDED,
    WORKFLOW_ACTION_URLS,
    WORKFLOW_LABELS,
    fetch_ai_workflow_runs,
)
from app.utils.streamlit_date_input import normalize_date_range

st.set_page_config(page_title="AI workflow usage", page_icon=":material/smart_toy:", layout="wide")

GROUPING_FREQ: dict[str, str] = {"Day": "D", "Week": "W", "Month": "M"}
WORKFLOW_COLORS: dict[str, str] = {
    "AI PR Review": "#5B8FF9",
    "AI QA Testing": "#5AD8A6",
    "AI Issue Triage": "#F6BD16",
}
OUTCOME_COLORS: dict[str, str] = {
    OUTCOME_SUCCEEDED: "#2BBD7E",
    OUTCOME_FAILED: "#FF4B4B",
    OUTCOME_CANCELLED: "#8B8E97",
}
OUTCOME_OPTIONS: tuple[str, ...] = (OUTCOME_SUCCEEDED, OUTCOME_FAILED, OUTCOME_CANCELLED)
SPARKLINE_DAYS: int = 30
METRIC_CARD_HEIGHT: int = 240


def _as_naive_utc(series: pd.Series) -> pd.Series:
    values = pd.to_datetime(series, utc=True, errors="coerce")
    return values.dt.tz_localize(None)


def _period_start(series: pd.Series, grouping: str) -> pd.Series:
    freq = GROUPING_FREQ[grouping]
    return _as_naive_utc(series).dt.to_period(freq).dt.start_time


def _period_heading(grouping: str, period_start: datetime) -> str:
    if grouping == "Day":
        return f"Runs for {period_start.strftime('%b %d, %Y')}"
    if grouping == "Week":
        return f"Runs for week of {period_start.strftime('%b %d, %Y')}"
    return f"Runs for {period_start.strftime('%B %Y')}"


def _format_duration(seconds: Any) -> str:
    if seconds is None or pd.isna(seconds):
        return "—"
    duration = float(seconds)
    if duration < 0:
        return "—"
    total_seconds = int(duration)
    minutes, secs = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _signed_duration_delta(current: Any, previous: Any) -> str | None:
    if current is None or previous is None or pd.isna(current) or pd.isna(previous):
        return None
    diff = float(current) - float(previous)
    if diff == 0:
        return "0s this week"
    sign = "+" if diff > 0 else "-"
    return f"{sign}{_format_duration(abs(diff))} this week"


def _sparkline(series: pd.Series, days: pd.Index, *, fill: float | None = None) -> list[float] | None:
    if len(days) < 2:
        return None
    values = pd.to_numeric(series, errors="coerce")
    values.index = pd.Index(pd.to_datetime(values.index, errors="coerce").date)
    values = values.groupby(level=0).mean()
    aligned = values.reindex(days)
    aligned = aligned.fillna(fill) if fill is not None else aligned.ffill().bfill()
    aligned = aligned.fillna(0.0)
    return [float(value) for value in aligned.tolist()]


def _sparkline_index(start: date, end: date) -> pd.Index:
    window_end = end
    window_start = max(start, window_end - timedelta(days=SPARKLINE_DAYS - 1))
    return pd.Index([window_start + timedelta(days=offset) for offset in range((window_end - window_start).days + 1)])


def _success_rate(outcomes: pd.Series) -> float | None:
    completed = outcomes.isin([OUTCOME_SUCCEEDED, OUTCOME_FAILED])
    completed_count = int(completed.sum())
    if completed_count == 0:
        return None
    return float((outcomes[completed] == OUTCOME_SUCCEEDED).mean() * 100)


def _week_bounds(today: date) -> tuple[date, date]:
    this_week_start = today - timedelta(days=today.weekday())
    last_week_start = this_week_start - timedelta(days=7)
    return last_week_start, this_week_start


def _pr_url(pr_number: Any) -> str | None:
    if pr_number is None or pd.isna(pr_number):
        return None
    return f"https://github.com/streamlit/streamlit/pull/{int(pr_number)}"


def _selected_period_timestamp(value: Any, grouping: str) -> pd.Timestamp:
    selected_ts = pd.Timestamp(value)
    if selected_ts.tzinfo is not None:
        selected_ts = selected_ts.tz_convert("UTC").tz_localize(None)
    return selected_ts.to_period(GROUPING_FREQ[grouping]).to_timestamp()


def _as_str_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


title_row = st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center")
with title_row:
    st.title(":material/smart_toy: AI workflow usage")
    actions = st.container(horizontal=True, vertical_alignment="center", width="content")
    with actions:
        filters_slot = st.container(width="content")
        if st.button(":material/refresh: Refresh data", type="tertiary"):
            fetch_ai_workflow_runs.clear()

st.caption(
    "Runs of Streamlit's Cursor CLI GitHub Actions: "
    f"[AI PR Review]({WORKFLOW_ACTION_URLS['AI PR Review']}), "
    f"[AI QA Testing]({WORKFLOW_ACTION_URLS['AI QA Testing']}), and "
    f"[AI Issue Triage]({WORKFLOW_ACTION_URLS['AI Issue Triage']}). "
    "Skipped runs from unrelated label events are excluded."
)

runs, fetch_errors = fetch_ai_workflow_runs()
for error in fetch_errors:
    st.warning(error)

if not runs:
    st.info("No AI workflow runs found.")
    st.stop()

runs_df = pd.DataFrame(runs)
runs_df["created_at"] = _as_naive_utc(runs_df["created_at"])
runs_df["run_started_at"] = _as_naive_utc(runs_df["run_started_at"])
runs_df["updated_at"] = _as_naive_utc(runs_df["updated_at"])
runs_df = runs_df.dropna(subset=["created_at"])
runs_df["duration_seconds"] = (runs_df["updated_at"] - runs_df["run_started_at"]).dt.total_seconds()
runs_df["created_date"] = runs_df["created_at"].dt.date
runs_df["target_url"] = runs_df["pr_number"].map(_pr_url)
runs_df["run_url"] = runs_df["html_url"]

min_date = runs_df["created_date"].min()
max_date = runs_df["created_date"].max()
today = date.today()

with filters_slot:
    with st.popover("Filters", icon=":material/filter_list:", type="tertiary", width="content"):
        selected_workflows = st.pills(
            "Workflows",
            options=list(WORKFLOW_LABELS),
            default=list(WORKFLOW_LABELS),
            selection_mode="multi",
            key="ai_usage_workflows",
        )
        selected_outcomes = st.pills(
            "Outcomes",
            options=list(OUTCOME_OPTIONS),
            default=[OUTCOME_SUCCEEDED, OUTCOME_FAILED],
            selection_mode="multi",
            key="ai_usage_outcomes",
        )
        ignore_cancelled = st.toggle(
            "Ignore cancelled runs",
            value=True,
            help="Cancelled runs are usually superseded by a newer run. Ignoring them keeps counts and average runtime from being skewed by short, incomplete jobs.",
            key="ai_usage_ignore_cancelled",
        )
        date_range = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max(max_date, today),
            key="ai_usage_date_range",
        )

selected_workflows = _as_str_list(selected_workflows)
selected_outcomes = _as_str_list(selected_outcomes)

start_date, end_date = normalize_date_range(date_range)
if start_date is None:
    start_date = min_date
if end_date is None:
    end_date = max_date

filtered_df = runs_df[
    runs_df["workflow"].isin(selected_workflows)
    & runs_df["outcome"].isin(selected_outcomes)
    & (runs_df["created_date"] >= start_date)
    & (runs_df["created_date"] <= end_date)
].copy()
if ignore_cancelled:
    filtered_df = filtered_df[filtered_df["outcome"] != OUTCOME_CANCELLED]

if filtered_df.empty:
    st.info("No runs match the selected filters.")
    st.stop()

last_week_start, this_week_start = _week_bounds(today)
this_week_df = filtered_df[filtered_df["created_date"] >= this_week_start]
last_week_df = filtered_df[
    (filtered_df["created_date"] >= last_week_start) & (filtered_df["created_date"] < this_week_start)
]
runtime_df = filtered_df[filtered_df["duration_seconds"].notna() & (filtered_df["duration_seconds"] >= 0)].copy()
runtime_df["duration_minutes"] = runtime_df["duration_seconds"] / 60
this_week_runtime = runtime_df[runtime_df["created_date"] >= this_week_start]
last_week_runtime = runtime_df[
    (runtime_df["created_date"] >= last_week_start) & (runtime_df["created_date"] < this_week_start)
]
overall_success_rate = _success_rate(filtered_df["outcome"])
failed_count = int((filtered_df["outcome"] == OUTCOME_FAILED).sum())
avg_duration = runtime_df["duration_seconds"].mean() if not runtime_df.empty else None
median_duration = runtime_df["duration_seconds"].median() if not runtime_df.empty else None
this_week_rate = _success_rate(this_week_df["outcome"])
last_week_rate = _success_rate(last_week_df["outcome"])
this_week_failed = int((this_week_df["outcome"] == OUTCOME_FAILED).sum())
last_week_failed = int((last_week_df["outcome"] == OUTCOME_FAILED).sum())
this_week_avg = this_week_runtime["duration_seconds"].mean() if not this_week_runtime.empty else None
last_week_avg = last_week_runtime["duration_seconds"].mean() if not last_week_runtime.empty else None
this_week_median = this_week_runtime["duration_seconds"].median() if not this_week_runtime.empty else None
last_week_median = last_week_runtime["duration_seconds"].median() if not last_week_runtime.empty else None
rate_delta = (
    f"{this_week_rate - last_week_rate:+.0f} pp this week"
    if this_week_rate is not None and last_week_rate is not None
    else None
)

completed_df = filtered_df[filtered_df["outcome"].isin([OUTCOME_SUCCEEDED, OUTCOME_FAILED])]
daily_counts = filtered_df.groupby("created_date").size().sort_index()
sparkline_days = _sparkline_index(start_date, end_date)
daily_success_rate = (
    (completed_df["outcome"] == OUTCOME_SUCCEEDED).groupby(completed_df["created_date"]).mean().mul(100).sort_index()
    if not completed_df.empty
    else pd.Series(dtype="float64")
)
daily_failed = filtered_df[filtered_df["outcome"] == OUTCOME_FAILED].groupby("created_date").size().sort_index()
daily_avg_duration = (
    runtime_df.groupby("created_date")["duration_seconds"].mean().sort_index()
    if not runtime_df.empty
    else pd.Series(dtype="float64")
)
daily_median_duration = (
    runtime_df.groupby("created_date")["duration_seconds"].median().sort_index()
    if not runtime_df.empty
    else pd.Series(dtype="float64")
)

runs_sparkline = _sparkline(daily_counts, sparkline_days, fill=0)
success_sparkline = _sparkline(daily_success_rate, sparkline_days)
failed_sparkline = _sparkline(daily_failed, sparkline_days, fill=0)
avg_duration_sparkline = _sparkline(daily_avg_duration, sparkline_days)
median_duration_sparkline = _sparkline(daily_median_duration, sparkline_days)

metric_row = st.container(horizontal=True)
with metric_row:
    st.metric(
        "Runs",
        f"{len(filtered_df):,}",
        delta=f"{len(this_week_df) - len(last_week_df):+} this week",
        delta_color="off",
        border=True,
        height=METRIC_CARD_HEIGHT,
        chart_data=runs_sparkline,
        chart_type="line",
        help="Completed AI workflow runs in the selected filters. Weekly delta compares this calendar week to the previous one.",
    )
    st.metric(
        "Success rate",
        f"{overall_success_rate:.0f}%" if overall_success_rate is not None else "—",
        delta=rate_delta,
        delta_color="off",
        border=True,
        height=METRIC_CARD_HEIGHT,
        chart_data=success_sparkline,
        chart_type="line",
        help="Share of succeeded vs failed runs. Cancelled runs are excluded from this rate.",
    )
    st.metric(
        "Failed",
        f"{failed_count:,}",
        delta=f"{this_week_failed - last_week_failed:+} this week",
        delta_color="off",
        border=True,
        height=METRIC_CARD_HEIGHT,
        chart_data=failed_sparkline,
        chart_type="line",
        help="Runs that finished with failure, startup failure, or timeout.",
    )
    st.metric(
        "Average duration",
        _format_duration(avg_duration),
        delta=_signed_duration_delta(this_week_avg, last_week_avg),
        delta_color="off",
        border=True,
        height=METRIC_CARD_HEIGHT,
        chart_data=avg_duration_sparkline,
        chart_type="line",
        help="Mean time from start to finish for runs in the current filters.",
    )
    st.metric(
        "Median duration",
        _format_duration(median_duration),
        delta=_signed_duration_delta(this_week_median, last_week_median),
        delta_color="off",
        border=True,
        height=METRIC_CARD_HEIGHT,
        chart_data=median_duration_sparkline,
        chart_type="line",
        help="Median time from start to finish for runs in the current filters.",
    )

st.markdown("##### Runs")
with st.container(horizontal=True):
    for workflow in selected_workflows:
        workflow_df = filtered_df[filtered_df["workflow"] == workflow]
        rate = _success_rate(workflow_df["outcome"]) if not workflow_df.empty else None
        sparkline = _sparkline(workflow_df.groupby("created_date").size().sort_index(), sparkline_days, fill=0)
        st.metric(
            workflow,
            f"{len(workflow_df):,}",
            delta=f"{rate:.0f}% succeeded" if rate is not None else "No completed runs",
            delta_color="off",
            border=True,
            height=METRIC_CARD_HEIGHT,
            chart_data=sparkline,
            chart_type="line",
        )

if selected_workflows and not runtime_df.empty:
    st.markdown("##### Average runtime")
    with st.container(horizontal=True):
        for workflow in selected_workflows:
            workflow_runtime = runtime_df[runtime_df["workflow"] == workflow]
            workflow_avg = workflow_runtime["duration_seconds"].mean() if not workflow_runtime.empty else None
            sparkline = _sparkline(
                workflow_runtime.groupby("created_date")["duration_seconds"].mean().sort_index(),
                sparkline_days,
            )
            st.metric(
                workflow,
                _format_duration(workflow_avg),
                border=True,
                height=METRIC_CARD_HEIGHT,
                chart_data=sparkline,
                chart_type="line",
                help="Average time from start to finish for this workflow in the current filters.",
            )

chart_header = st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom")
with chart_header:
    heading_slot = st.container(width="content")
    grouping = st.segmented_control(
        "Group by",
        options=list(GROUPING_FREQ),
        default="Week",
        required=True,
        label_visibility="collapsed",
        width="content",
        key="ai_usage_grouping",
    )
if grouping is None:
    grouping = "Week"
with heading_slot:
    st.markdown(f"##### Runs by {grouping.lower()}")

filtered_df["period"] = _period_start(filtered_df["created_at"], grouping)
completed_df = filtered_df[filtered_df["outcome"].isin([OUTCOME_SUCCEEDED, OUTCOME_FAILED])]
runtime_df["period"] = _period_start(runtime_df["created_at"], grouping)

workflow_counts = (
    filtered_df.groupby(["period", "workflow"], as_index=False)
    .size()
    .rename(columns={"size": "runs"})
    .sort_values("period")
)
outcome_counts = (
    filtered_df.groupby(["period", "outcome"], as_index=False)
    .size()
    .rename(columns={"size": "runs"})
    .sort_values("period")
)

if completed_df.empty:
    success_rate_df = pd.DataFrame(columns=["period", "workflow", "success_rate"])
else:
    success_rate_df = (
        completed_df.assign(is_success=completed_df["outcome"] == OUTCOME_SUCCEEDED)
        .groupby(["period", "workflow"], as_index=False)
        .agg(total=("id", "count"), succeeded=("is_success", "sum"))
    )
    success_rate_df["success_rate"] = success_rate_df["succeeded"] / success_rate_df["total"] * 100

if runtime_df.empty:
    duration_by_period = pd.DataFrame(columns=["period", "workflow", "avg_minutes", "median_minutes"])
    duration_by_workflow = pd.DataFrame(columns=["workflow", "avg_minutes", "median_minutes"])
else:
    duration_by_period = runtime_df.groupby(["period", "workflow"], as_index=False).agg(
        avg_seconds=("duration_seconds", "mean"),
        median_seconds=("duration_seconds", "median"),
    )
    duration_by_period["avg_minutes"] = duration_by_period["avg_seconds"] / 60
    duration_by_period["median_minutes"] = duration_by_period["median_seconds"] / 60
    duration_by_workflow = runtime_df.groupby("workflow", as_index=False).agg(
        avg_seconds=("duration_seconds", "mean"),
        median_seconds=("duration_seconds", "median"),
        runs=("id", "count"),
    )
    duration_by_workflow["avg_minutes"] = duration_by_workflow["avg_seconds"] / 60
    duration_by_workflow["median_minutes"] = duration_by_workflow["median_seconds"] / 60

chart_tab_workflow, chart_tab_outcome, chart_tab_rate, chart_tab_duration = st.tabs(
    ["By workflow", "By outcome", "Success rate", "Duration"]
)

selected_period_start: datetime | None = None

with chart_tab_workflow:
    fig_workflow = px.bar(
        workflow_counts,
        x="period",
        y="runs",
        color="workflow",
        color_discrete_map=WORKFLOW_COLORS,
        labels={"period": grouping, "runs": "Runs", "workflow": "Workflow"},
        category_orders={"workflow": list(WORKFLOW_LABELS)},
    )
    fig_workflow.update_layout(bargap=0.15, legend_title="Workflow", xaxis_title=None, yaxis_title="Runs")
    workflow_selection = st.plotly_chart(
        fig_workflow,
        width="stretch",
        on_select="rerun",
        key="ai_runs_by_workflow",
    )
    st.caption(":material/web_traffic: Click a bar to inspect the runs in that period.")
    if workflow_selection and workflow_selection["selection"]["points"]:
        selected_period_start = pd.to_datetime(workflow_selection["selection"]["points"][0]["x"]).to_pydatetime()

with chart_tab_outcome:
    fig_outcome = px.bar(
        outcome_counts,
        x="period",
        y="runs",
        color="outcome",
        color_discrete_map=OUTCOME_COLORS,
        labels={"period": grouping, "runs": "Runs", "outcome": "Outcome"},
        category_orders={"outcome": list(OUTCOME_OPTIONS)},
    )
    fig_outcome.update_layout(bargap=0.15, legend_title="Outcome", xaxis_title=None, yaxis_title="Runs")
    outcome_selection = st.plotly_chart(
        fig_outcome,
        width="stretch",
        on_select="rerun",
        key="ai_runs_by_outcome",
    )
    st.caption(":material/web_traffic: Click a bar to inspect the runs in that period.")
    if selected_period_start is None and outcome_selection and outcome_selection["selection"]["points"]:
        selected_period_start = pd.to_datetime(outcome_selection["selection"]["points"][0]["x"]).to_pydatetime()

with chart_tab_rate:
    if success_rate_df.empty:
        st.info("No succeeded or failed runs in the selected filters.")
    else:
        fig_rate = px.line(
            success_rate_df,
            x="period",
            y="success_rate",
            color="workflow",
            markers=True,
            color_discrete_map=WORKFLOW_COLORS,
            labels={"period": grouping, "success_rate": "Success rate (%)", "workflow": "Workflow"},
            category_orders={"workflow": list(WORKFLOW_LABELS)},
        )
        fig_rate.update_layout(yaxis_range=[0, 100], xaxis_title=None, yaxis_title="Success rate (%)")
        st.plotly_chart(fig_rate, width="stretch")
        st.caption("Cancelled runs are excluded from the success rate.")

with chart_tab_duration:
    if runtime_df.empty:
        st.info("No duration data for the selected filters.")
    else:
        duration_stat = st.segmented_control(
            "Runtime statistic",
            options=["Average", "Median"],
            default="Average",
            key="ai_runtime_statistic",
        )
        if duration_stat is None:
            duration_stat = "Average"
        duration_column = "avg_minutes" if duration_stat == "Average" else "median_minutes"
        duration_label = f"{duration_stat} duration (min)"
        if ignore_cancelled:
            st.caption("Cancelled runs are excluded from runtime stats.")
        else:
            st.caption("Cancelled runs are included and are often much shorter than completed runs.")

        fig_duration = px.line(
            duration_by_period,
            x="period",
            y=duration_column,
            color="workflow",
            markers=True,
            color_discrete_map=WORKFLOW_COLORS,
            labels={
                "period": grouping,
                duration_column: duration_label,
                "workflow": "Workflow",
            },
            category_orders={"workflow": list(WORKFLOW_LABELS)},
        )
        fig_duration.update_layout(xaxis_title=None, yaxis_title=duration_label)
        st.plotly_chart(fig_duration, width="stretch")

        with st.container(horizontal=True, vertical_alignment="top"):
            fig_avg_bar = px.bar(
                duration_by_workflow,
                x="workflow",
                y=duration_column,
                color="workflow",
                color_discrete_map=WORKFLOW_COLORS,
                labels={"workflow": "Workflow", duration_column: duration_label},
                category_orders={"workflow": list(WORKFLOW_LABELS)},
            )
            fig_avg_bar.update_layout(
                title=f"{duration_stat} runtime by workflow",
                showlegend=False,
                xaxis_title=None,
                yaxis_title=duration_label,
            )
            st.plotly_chart(fig_avg_bar, width="stretch")

            fig_box = px.box(
                runtime_df,
                x="workflow",
                y="duration_minutes",
                color="workflow",
                color_discrete_map=WORKFLOW_COLORS,
                points="outliers",
                labels={"workflow": "Workflow", "duration_minutes": "Duration (min)"},
                category_orders={"workflow": list(WORKFLOW_LABELS)},
            )
            fig_box.update_layout(
                title="Runtime distribution",
                showlegend=False,
                xaxis_title=None,
                yaxis_title="Duration (min)",
            )
            st.plotly_chart(fig_box, width="stretch")

detail_df = filtered_df
if selected_period_start is not None:
    selected_ts = _selected_period_timestamp(selected_period_start, grouping)
    detail_df = filtered_df[filtered_df["period"] == selected_ts]
    st.markdown(f"##### {_period_heading(grouping, selected_ts.to_pydatetime())}")
else:
    st.markdown("##### Recent runs")

detail_view = detail_df.sort_values("created_at", ascending=False).head(200).copy()
detail_view["Duration"] = detail_view["duration_seconds"].map(_format_duration)
detail_view["Started"] = detail_view["created_at"]

st.dataframe(
    detail_view[
        [
            "Started",
            "workflow",
            "outcome",
            "display_title",
            "trigger",
            "actor",
            "Duration",
            "target_url",
            "run_url",
        ]
    ],
    column_config={
        "Started": st.column_config.DatetimeColumn("Started", format="MMM DD, YYYY HH:mm"),
        "workflow": st.column_config.TextColumn("Workflow"),
        "outcome": st.column_config.TextColumn("Outcome"),
        "display_title": st.column_config.TextColumn("Title", width="large"),
        "trigger": st.column_config.TextColumn("Trigger"),
        "actor": st.column_config.TextColumn("Triggered by"),
        "Duration": st.column_config.TextColumn("Duration"),
        "target_url": st.column_config.LinkColumn("PR", display_text="Open PR"),
        "run_url": st.column_config.LinkColumn("Run", display_text=":material/open_in_new:"),
    },
    hide_index=True,
    width="stretch",
)

if len(detail_df) > 200:
    st.caption(f"Showing the 200 most recent of {len(detail_df):,} runs in this selection.")
