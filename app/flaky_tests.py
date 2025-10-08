from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Final

import altair as alt
import pandas as pd
import streamlit as st

from app.utils.github_utils import (
    fetch_workflow_run_annotations,
    fetch_workflow_runs,
    fetch_workflow_runs_ids,
)

st.set_page_config(page_title="Flaky Tests", page_icon="🧫")

st.title("🧫 Flaky Tests")

workflow_runs_limit = st.sidebar.slider(
    "Number of workflow runs", min_value=100, max_value=1000, value=200, step=100
)

rolling_window_size = st.sidebar.slider(
    "Flaky trend window size", min_value=5, max_value=50, value=25, step=5
)

hide_expected_flaky_tests = st.sidebar.checkbox("Hide expected flaky tests", value=True, help="Test that are expected to be flaky and marked with additional reruns (pytest.mark.flaky(reruns=3))")

# Tests that are expected to be flaky and marked with additional reruns (pytest.mark.flaky(reruns=3))
# This list needs to be updated manually. The test is matched via startswith,
# so it can cover full test scrits or just individual test methods.
EXPECTED_FLAKY_TESTS: Final[list[str]] = [
    "st_video_test.py::test_video_end_time",
    "st_pydeck_chart_test.py",
    "st_file_uploader_test.py::test_uploads_directory_with_multiple_files",
    "st_file_uploader_test.py::test_directory_upload_with_file_type_filtering",
    "st_dataframe_interactions_test.py::test_csv_download_button_in_iframe_with_new_tab_host_config",
    "st_dataframe_interactions_test.py::test_csv_download_button_in_iframe",
    "st_video_test.py::test_video_end_time_loop",
]


def is_expected_flaky(test_full_name: str) -> bool:
    """Return True if the given test name matches an expected flaky test prefix.

    The match uses startswith to allow both whole-script and single-test prefixes.
    """
    for expected_prefix in EXPECTED_FLAKY_TESTS:
        if test_full_name.startswith(expected_prefix):
            return True
    return False

# Fetch workflow runs
flaky_tests: Counter[str] = Counter()
example_run: dict[str, str] = {}
last_failure_date: dict[str, date] = {}
first_failure_date: dict[str, date] = {}
first_date = date.today()


workflow_runs = fetch_workflow_runs(
    "playwright.yml", limit=workflow_runs_limit, branch=None, status="success"
)
with st.spinner("Fetching workflow annotations..."):
    for workflow_run in workflow_runs:
        check_suite_id = workflow_run["check_suite_id"]
        workflow_date = date.fromisoformat(workflow_run["created_at"][:10])
        if workflow_date < first_date:
            first_date = workflow_date

        check_runs_ids = fetch_workflow_runs_ids(check_suite_id)
        for check_run_id in check_runs_ids:
            annotations_list = fetch_workflow_run_annotations(check_run_id)
            for annotation in annotations_list:
                if annotation["path"].startswith("e2e_playwright/"):
                    test_name = (
                        annotation["path"].replace("e2e_playwright/", "")
                        + "::"
                        + annotation["message"].split("\n\n")[0]
                    )
                    flaky_tests.update([test_name])
                    if test_name not in example_run:
                        example_run[test_name] = workflow_run["html_url"]
                    if test_name not in last_failure_date:
                        last_failure_date[test_name] = workflow_date
                    if test_name not in first_failure_date:
                        first_failure_date[test_name] = workflow_date
                    elif workflow_date < first_failure_date[test_name]:
                        first_failure_date[test_name] = workflow_date

flaky_tests_df = pd.DataFrame(flaky_tests.items(), columns=["Test Name", "Failures"])
# Set the test name as the index
flaky_tests_df = flaky_tests_df.set_index("Test Name")
flaky_tests_df = flaky_tests_df.sort_values("Failures", ascending=False)
flaky_tests_df["Latest Run"] = flaky_tests_df.index.map(example_run)
flaky_tests_df["Test Script"] = flaky_tests_df.index.map(
    lambda x: "https://github.com/streamlit/streamlit/blob/develop/e2e_playwright/"
    + x.split(":")[0]
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

overall_failure_prob = 1 - (1 - flaky_tests_df["Workflow Failure Probability"].fillna(0)).prod()


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
    use_container_width=True,
    column_config={
        "Test Name": st.column_config.TextColumn(width="large"),
        "Last Failure Date": st.column_config.DatetimeColumn(
            "Last Failure Date", format="distance"
        ),
        "First Failure Date": st.column_config.DatetimeColumn(
            "First Failure Date", format="distance"
        ),
        "Latest Run": st.column_config.LinkColumn(display_text="Open"),
        "Test Script": st.column_config.LinkColumn(display_text="Open"),
        "Workflow Failure Probability": st.column_config.ProgressColumn(
            "Workflow Failure Probability", format="percent", help="The approximate probability that this test causes a workflow failure."
        ),
    },
)

st.divider()
# Process workflow runs to determine which ones needed reruns
workflow_data = []
for workflow_run in workflow_runs:
    run_date = datetime.fromisoformat(workflow_run["created_at"].replace("Z", "+00:00"))
    check_suite_id = workflow_run["check_suite_id"]

    # Check if this workflow run had any annotations (indicating reruns)
    had_reruns = False
    check_runs_ids = fetch_workflow_runs_ids(check_suite_id)
    for check_run_id in check_runs_ids:
        annotations_list = fetch_workflow_run_annotations(check_run_id)
        if hide_expected_flaky_tests:
            # Only consider reruns from non-expected flaky tests
            for annotation in annotations_list:
                if annotation["path"].startswith("e2e_playwright/"):
                    test_name_for_chart = (
                        annotation["path"].replace("e2e_playwright/", "")
                        + "::"
                        + annotation["message"].split("\n\n")[0]
                    )
                    if not is_expected_flaky(test_name_for_chart):
                        had_reruns = True
                        break
            if had_reruns:
                break
        else:
            if any(
                annotation["path"].startswith("e2e_playwright/")
                for annotation in annotations_list
            ):
                had_reruns = True
                break

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
workflow_df["rolling_avg"] = (
    workflow_df["had_reruns_int"]
    .rolling(window=rolling_window_size, min_periods=10)
    .mean()
)

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
                alt.Tooltip(
                    "rolling_avg:Q", title="Ratio with Test Reruns", format=".1%"
                ),
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
        .encode(
            y="y:Q", tooltip=[alt.Tooltip("y:Q", title="Overall Average", format=".1%")]
        )
    )

    # Combine the charts
    chart = line_chart + rule

    st.altair_chart(chart, use_container_width=True)

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
