from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from app.utils.github_utils import (
    EXPECTED_FLAKY_TESTS,
    fetch_workflow_run_annotations,
    fetch_workflow_runs,
    fetch_workflow_runs_ids,
)

st.set_page_config(page_title="Flaky tests", page_icon="🧫")

title_row = st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center")
with title_row:
    st.title("🧫 Flaky tests")
    if st.button(":material/refresh: Refresh Data", type="tertiary"):
        fetch_workflow_runs.clear()

workflow_runs_limit = st.sidebar.slider("Number of workflow runs", min_value=100, max_value=1000, value=200, step=100)

rolling_window_size = st.sidebar.slider("Flaky trend window size", min_value=5, max_value=50, value=25, step=5)

hide_expected_flaky_tests = st.sidebar.checkbox(
    "Hide expected flaky tests",
    value=True,
    help="Test that are expected to be flaky and marked with additional reruns (pytest.mark.flaky(reruns=3))",
)


def is_expected_flaky(test_full_name: str) -> bool:
    """Return True if the given test name matches an expected flaky test prefix.

    The match uses startswith to allow both whole-script and single-test prefixes.
    """
    return any(test_full_name.startswith(expected_prefix) for expected_prefix in EXPECTED_FLAKY_TESTS)


def extract_playwright_test_name(annotation: dict[str, Any]) -> str | None:
    """Extract a normalized test name from a Playwright annotation."""
    path = str(annotation.get("path", ""))
    if not path.startswith("e2e_playwright/"):
        return None

    message = str(annotation.get("message", ""))
    return f"{path.replace('e2e_playwright/', '')}::{message.split('\n\n', maxsplit=1)[0]}"


@st.cache_data(ttl=60 * 60 * 6, max_entries=1024, show_spinner=False)
def fetch_check_suite_playwright_tests(check_suite_id: str) -> list[str]:
    """Fetch all Playwright test names attached to a check suite."""
    test_names: list[str] = []
    check_runs_ids = fetch_workflow_runs_ids(check_suite_id)
    for check_run_id in check_runs_ids:
        annotations_list = fetch_workflow_run_annotations(check_run_id)
        for annotation in annotations_list:
            test_name = extract_playwright_test_name(annotation)
            if test_name:
                test_names.append(test_name)
    return test_names


def build_workflow_annotation_snapshot(workflow_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expand check-suite annotations once and reuse across all sections."""
    return [
        {
            "date": date.fromisoformat(workflow_run["created_at"][:10]),
            "html_url": workflow_run["html_url"],
            "tests": fetch_check_suite_playwright_tests(workflow_run["check_suite_id"]),
        }
        for workflow_run in workflow_runs
    ]


# Fetch workflow runs
flaky_tests: Counter[str] = Counter()
example_run: dict[str, str] = {}
last_failure_date: dict[str, date] = {}
first_failure_date: dict[str, date] = {}
first_date = date.today()


workflow_runs = fetch_workflow_runs("playwright.yml", limit=workflow_runs_limit, branch=None, status="success")
with st.spinner("Fetching workflow annotations..."):
    workflow_snapshot = build_workflow_annotation_snapshot(workflow_runs)
    for workflow_run in workflow_snapshot:
        workflow_date = workflow_run["date"]
        first_date = min(first_date, workflow_date)

        for test_name in workflow_run["tests"]:
            flaky_tests.update([test_name])
            if test_name not in example_run:
                example_run[test_name] = workflow_run["html_url"]
            if test_name not in last_failure_date:
                last_failure_date[test_name] = workflow_date
            if test_name not in first_failure_date or workflow_date < first_failure_date[test_name]:
                first_failure_date[test_name] = workflow_date

flaky_tests_df = pd.DataFrame(flaky_tests.items(), columns=["Test Name", "Failures"])
# Set the test name as the index
flaky_tests_df = flaky_tests_df.set_index("Test Name")
flaky_tests_df = flaky_tests_df.sort_values("Failures", ascending=False)
flaky_tests_df["Latest Run"] = flaky_tests_df.index.map(example_run)
flaky_tests_df["Test Script"] = flaky_tests_df.index.map(
    lambda x: "https://github.com/streamlit/streamlit/blob/develop/e2e_playwright/" + x.split(":")[0]
)
flaky_tests_df["Last Failure Date"] = flaky_tests_df.index.map(last_failure_date)
flaky_tests_df["First Failure Date"] = flaky_tests_df.index.map(first_failure_date)

# Optionally hide expected flaky tests from the table and downstream calculations
if hide_expected_flaky_tests and not flaky_tests_df.empty:
    mask_not_expected = ~flaky_tests_df.index.to_series().apply(is_expected_flaky)
    flaky_tests_df = flaky_tests_df[mask_not_expected]


def extract_browser(test_name: str) -> str | None:
    for browser in ["chromium", "firefox", "webkit"]:
        if browser in test_name:
            return browser
    return None


flaky_tests_df["Browser"] = flaky_tests_df.index.map(extract_browser)


# Estimate per-test probability of causing a workflow failure
# Let p be the per-run probability a test fails on the first attempt.
# Using a simple approximation with available data, estimate p as:
#   p ≈ reruns / total_successful_runs
# Then the probability this test causes a workflow failure (fails twice) is p^2.
total_successful_runs = len(workflow_runs)

# Single adjusted estimate of workflow failure probability per test
# x = reruns / successful_runs; p_adj = x/(1-x); failure probability = p_adj^2
if total_successful_runs > 0:
    x_series = (flaky_tests_df["Failures"] / total_successful_runs).clip(upper=0.499999)
    flaky_tests_df["Workflow Failure Probability"] = (x_series / (1 - x_series)) ** 2
else:
    flaky_tests_df["Workflow Failure Probability"] = float("nan")

overall_failure_prob: float = 1 - (1 - flaky_tests_df["Workflow Failure Probability"].fillna(0).astype(float)).prod()  # type: ignore[operator,assignment]


total_flaky_failures = int(flaky_tests_df["Failures"].sum())
top5_reduction_pct = 0.0
if total_flaky_failures > 0:
    top5_reduction_pct = round(flaky_tests_df[:5]["Failures"].sum() / total_flaky_failures * 100, 2)

st.caption(
    f"**{total_flaky_failures} flaky reruns** in the "
    f"last **{workflow_runs_limit} successful workflow runs** ({first_date}) impacting "
    f"**{len(flaky_tests_df)} e2e tests** in **{len(flaky_tests_df['Test Script'].unique())} "
    f"test scripts**. Fixing the top 5 flaky tests would reduce flaky reruns by "
    f"**{top5_reduction_pct}%**. "
    f"The approximate probability of a workflow run failing due to flakiness is **{overall_failure_prob:.1%}**."
)
st.dataframe(
    flaky_tests_df,
    width="stretch",
    column_config={
        "Test Name": st.column_config.TextColumn(width="large"),
        "Last Failure Date": st.column_config.DatetimeColumn("Last Failure Date", format="distance"),
        "First Failure Date": st.column_config.DatetimeColumn("First Failure Date", format="distance"),
        "Latest Run": st.column_config.LinkColumn(display_text="Open"),
        "Test Script": st.column_config.LinkColumn(display_text="Open"),
        "Workflow Failure Probability": st.column_config.ProgressColumn(
            "Workflow Failure Probability",
            format="percent",
            help="The approximate probability that this test causes a workflow failure.",
        ),
    },
)

st.divider()
# Process workflow runs to determine which ones needed reruns
workflow_data = []
for workflow_run in workflow_snapshot:
    run_date = datetime.combine(workflow_run["date"], datetime.min.time())
    tests_for_run = workflow_run["tests"]
    if hide_expected_flaky_tests:
        had_reruns = any(not is_expected_flaky(test_name) for test_name in tests_for_run)
    else:
        had_reruns = bool(tests_for_run)

    workflow_data.append(
        {
            "date": run_date.date(),
            "had_reruns": had_reruns,
        }
    )

# Convert to DataFrame and sort by date
workflow_df = pd.DataFrame(workflow_data)
workflow_df = workflow_df.sort_values("date")

# Calculate rolling average
workflow_df["had_reruns_int"] = workflow_df["had_reruns"].astype(int)
workflow_df["rolling_avg"] = workflow_df["had_reruns_int"].rolling(window=rolling_window_size, min_periods=10).mean()

# Aggregate by day - take the last value for each day
workflow_daily_df = workflow_df.groupby("date").last().reset_index()

# Create the chart
if not workflow_df.empty:
    # Calculate overall average for reference line
    overall_avg = workflow_df["had_reruns_int"].mean()

    # Format the tooltip to show percentage
    line_chart = (
        alt.Chart(workflow_daily_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %d")),
            y=alt.Y(
                "rolling_avg:Q",
                title="Runs with Test Reruns",
                scale=alt.Scale(domain=[0, 1]),
                axis=alt.Axis(format=".0%"),
            ),
            tooltip=[
                alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
                alt.Tooltip("rolling_avg:Q", title="Ratio with Test Reruns", format=".1%"),
            ],
        )
        .properties(
            title="Rolling Average of Workflow Runs Needing Test Reruns",
            width="container",
            height=300,
        )
    )

    # Add a rule for the overall average
    rule = (
        alt.Chart(pd.DataFrame({"y": [overall_avg]}))
        .mark_rule(
            strokeDash=[12, 6],
            strokeWidth=1,
            color="red",
        )
        .encode(y="y:Q", tooltip=[alt.Tooltip("y:Q", title="Overall Average", format=".1%")])
    )

    # Combine the charts
    chart = line_chart + rule

    st.altair_chart(chart, width="stretch")

    st.caption(
        f"This chart shows the rolling average (window of {rolling_window_size} runs) of the proportion of workflow runs "
        "that needed at least one test rerun due to flaky tests. A lower value is better. "
        f"The overall average across all {workflow_runs_limit} runs is {overall_avg:.1%}."
    )

    with st.expander(":material/info: How to interpret this chart"):
        st.markdown(
            f"""
        This chart shows a rolling average of the last {rolling_window_size} workflow runs for each day. Here's how to interpret it:

        - Each point represents the average flakiness rate of the most recent {rolling_window_size} workflow runs as of that day
        - The value can remain constant across multiple days if:
          - No new workflow runs occurred on those days
          - New runs had the same flakiness status (all flaky or all non-flaky)
          - The oldest runs leaving the window had the same flakiness status as the new ones entering

        Adjust the "Rolling average window size" in the sidebar to change the sensitivity of the trend line.
        """
        )
else:
    st.warning("Not enough data to generate the trend chart.")
