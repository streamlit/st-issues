from __future__ import annotations

from collections import Counter
from datetime import date

import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Flaky Tests", page_icon="🧫", initial_sidebar_state="collapsed"
)

st.title("🧫 Flaky Tests")

GITHUB_API_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token {st.secrets['github']['token']}",
}

workflow_runs_limit = st.sidebar.slider(
    "Number of workflow runs", min_value=100, max_value=1000, value=300, step=100
)


@st.cache_data(
    ttl=60 * 60 * 48, show_spinner="Fetching workflow runs..."
)  # cache for 48 hours
def fetch_workflow_runs(workflow_name: str, limit: int = 100) -> list[dict]:
    all_runs = []
    page = 0
    per_page = 100  # GitHub API maximum per page

    while len(all_runs) < limit:
        params = {"per_page": min(per_page, limit - len(all_runs)), "page": page}
        response = requests.get(
            f"https://api.github.com/repos/streamlit/streamlit/actions/workflows/{workflow_name}/runs",
            headers=GITHUB_API_HEADERS,
            params=params,
        )

        if response.status_code != 200:
            st.error(f"Error fetching data: {response.status_code}")
            break

        runs = response.json()["workflow_runs"]
        all_runs.extend(runs)

        if len(runs) < per_page:
            break  # No more pages to fetch

        page += 1

    return all_runs[:limit]


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
flaky_tests = Counter()
example_run = {}
first_date = date.today()

workflow_runs = fetch_workflow_runs("playwright.yml", limit=workflow_runs_limit)
with st.spinner("Fetching workflow annotations..."):
    for workflow_run in workflow_runs:
        check_suite_id = workflow_run["check_suite_id"]
        workflow_date = date.fromisoformat(workflow_run["created_at"][:10])
        if workflow_date < first_date:
            first_date = workflow_date

        check_runs_ids = fetch_check_runs_ids(check_suite_id)
        for check_run_id in check_runs_ids:
            annotations = fetch_annotations(check_run_id)
            for annotation in annotations:
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

top_flaky_tests = flaky_tests_df[:10]


st.caption(
    f"**{flaky_tests_df['Failures'].sum()} flaky reruns** in the "
    f"last **{workflow_runs_limit} successful workflow runs** ({first_date}) impacting "
    f"**{len(flaky_tests_df)} e2e tests** in **{len(flaky_tests_df['Test Script'].unique())} "
    f"test scripts**. Fixing the top 10 flaky tests would reduce flaky reruns by "
    f"**{round(flaky_tests_df[:10]['Failures'].sum() / flaky_tests_df['Failures'].sum() * 100, 2)}%**."
)
st.dataframe(
    flaky_tests_df,
    use_container_width=True,
    column_config={
        "Latest Run": st.column_config.LinkColumn(display_text="Open"),
        "Test Script": st.column_config.LinkColumn(display_text="Open"),
    },
)
