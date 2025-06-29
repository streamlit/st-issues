from __future__ import annotations

from collections import Counter
from datetime import date, datetime

import altair as alt
import pandas as pd
import requests
import streamlit as st

from app.utils.github_utils import GITHUB_API_HEADERS, fetch_workflow_runs

st.set_page_config(page_title="Flaky Tests", page_icon="🧫")

st.title("🧫 Flaky Tests")

workflow_runs_limit = st.sidebar.slider(
    "Number of workflow runs", min_value=100, max_value=1000, value=300, step=100
)

rolling_window_size = st.sidebar.slider(
    "Flaky trend window size", min_value=5, max_value=50, value=25, step=5
)


@st.cache_data(show_spinner=False)
def fetch_check_runs_ids(check_suite_id: str) -> list[str]:
    annotations_url = f"https://api.github.com/repos/streamlit/streamlit/check-suites/{check_suite_id}/check-runs"
    response = requests.get(annotations_url, headers=GITHUB_API_HEADERS)

    if response.status_code == 200:
        check_runs = response.json()["check_runs"]
        check_runs = [
            check_run
            for check_run in check_runs
            if check_run["conclusion"] == "success"
        ]
        return [check_run["id"] for check_run in check_runs]
    st.error(f"Error fetching annotations: {response.status_code}")
    return []


@st.cache_data(show_spinner=False)
def fetch_annotations(check_run_id: str) -> list[dict]:
    annotations_url = f"https://api.github.com/repos/streamlit/streamlit/check-runs/{check_run_id}/annotations"
    response = requests.get(annotations_url, headers=GITHUB_API_HEADERS)

    if response.status_code == 200:
        return response.json()
    st.error(f"Error fetching annotations: {response.status_code}")
    return []


# Fetch workflow runs
flaky_tests: Counter[str] = Counter()
example_run: dict[str, str] = {}
first_date = date.today()

workflow_runs = fetch_workflow_runs(
    "playwright.yml", limit=workflow_runs_limit, branch=None, status=None
)
with st.spinner("Fetching workflow annotations..."):
    for workflow_run in workflow_runs:
        check_suite_id = workflow_run["check_suite_id"]
        workflow_date = date.fromisoformat(workflow_run["created_at"][:10])
        if workflow_date < first_date:
            first_date = workflow_date

        check_runs_ids = fetch_check_runs_ids(check_suite_id)
        for check_run_id in check_runs_ids:
            annotations_list = fetch_annotations(check_run_id)
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


flaky_tests_df = pd.DataFrame(flaky_tests.items(), columns=["Test Name", "Failures"])
# Set the test name as the index
flaky_tests_df = flaky_tests_df.set_index("Test Name")
flaky_tests_df = flaky_tests_df.sort_values("Failures", ascending=False)
flaky_tests_df["Latest Run"] = flaky_tests_df.index.map(example_run)
flaky_tests_df["Test Script"] = flaky_tests_df.index.map(
    lambda x: "https://github.com/streamlit/streamlit/blob/develop/e2e_playwright/"
    + x.split(":")[0]
)


def extract_browser(test_name: str) -> str | None:
    for browser in ["chromium", "firefox", "webkit"]:
        if browser in test_name:
            return browser
    return None


flaky_tests_df["Browser"] = flaky_tests_df.index.map(extract_browser)


st.caption(
    f"**{flaky_tests_df['Failures'].sum()} flaky reruns** in the "
    f"last **{workflow_runs_limit} successful workflow runs** ({first_date}) impacting "
    f"**{len(flaky_tests_df)} e2e tests** in **{len(flaky_tests_df['Test Script'].unique())} "
    f"test scripts**. Fixing the top 5 flaky tests would reduce flaky reruns by "
    f"**{round(flaky_tests_df[:5]['Failures'].sum() / flaky_tests_df['Failures'].sum() * 100, 2)}%**."
)
st.dataframe(
    flaky_tests_df,
    use_container_width=True,
    column_config={
        "Latest Run": st.column_config.LinkColumn(display_text="Open"),
        "Test Script": st.column_config.LinkColumn(display_text="Open"),
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
    check_runs_ids = fetch_check_runs_ids(check_suite_id)
    for check_run_id in check_runs_ids:
        annotations_list = fetch_annotations(check_run_id)
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
