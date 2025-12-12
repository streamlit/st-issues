import concurrent.futures
from typing import List, Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from app.perf import pytest_interpreting_results, pytest_writing_a_test
from app.perf.utils.artifacts import get_artifact_results
from app.perf.utils.perf_github_artifacts import get_commit_hashes_for_branch_name
from app.perf.utils.pytest_types import OutputJson
from app.perf.utils.tab_nav import segmented_tabs

TITLE = "Streamlit Performance - Pytest"

st.set_page_config(page_title=TITLE, layout="wide")

title_row = st.container(
    horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"
)
with title_row:
    st.title("🧪 Performance - Pytest")

tab = segmented_tabs(
    options=["Runs", "Interpret metrics", "Write a test"],
    key="pytest_tab",
    query_param="tab",
    default="Runs",
)

if tab != "Runs":
    if tab == "Interpret metrics":
        pytest_interpreting_results.render_interpreting_results()
    elif tab == "Write a test":
        pytest_writing_a_test.render_writing_a_test()
    st.stop()

token = st.secrets["github"]["token"]

if token is None:
    st.error("No GitHub token provided")
    st.stop()


@st.cache_data(ttl=60 * 60 * 12)
def get_commits(branch_name: str, limit: int = 50):
    return get_commit_hashes_for_branch_name(branch_name, limit=limit)


@st.cache_data(ttl=60 * 60 * 12)
def get_pytest_results(hash: str):
    return get_artifact_results(hash, "pytest")


commit_hashes = get_commits("develop")


directories: List[str] = []
timestamps: List[str] = []
results_by_run: list[OutputJson] = []

# Download all the artifacts for the performance runs in parallel
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(get_pytest_results, run_id) for run_id in commit_hashes]
    for future in concurrent.futures.as_completed(futures):
        result = future.result()

        results, timestamp = result

        if not results or not timestamp:
            continue

        results_by_run.append(results)
        timestamps.append(timestamp)

# Guard: no data found
if not results_by_run:
    st.info("No Pytest benchmark artifacts found for the selected commits.")
    st.stop()

# Sort results and timestamps based on timestamps
sorted_results_timestamps = sorted(
    zip(results_by_run, timestamps), key=lambda x: x[1]
)
results_by_run, timestamps = zip(*sorted_results_timestamps)


all_tests = set()
processed_results = {}
benchmark_data = []

for results in results_by_run:
    for test in results["benchmarks"]:
        all_tests.add(test["name"])

        if test["name"] not in processed_results:
            processed_results[test["name"]] = test["stats"]

        benchmark_data.append(
            {
                "test_name": test["name"],
                "min": test["stats"]["min"],
                "max": test["stats"]["max"],
                "mean": test["stats"]["mean"],
                "stddev": test["stats"]["stddev"],
                "median": test["stats"]["median"],
                "iqr": test["stats"]["iqr"],
                "q1": test["stats"]["q1"],
                "q3": test["stats"]["q3"],
                "iterations": test["stats"]["iterations"],
            }
        )

df = pd.DataFrame(benchmark_data)

if df.empty:
    st.info("No benchmark data found in the downloaded artifacts.")
    st.stop()

grid = st.container(horizontal=True, gap="medium")

all_tests = sorted(all_tests)

for index, test_name in enumerate(all_tests):
    test_df = df[df["test_name"] == test_name].reset_index()
    fig = px.box(
        test_df,
        x=test_df.index,
        y=["min", "q1", "median", "q3", "max"],
        points=None,
        title=test_name,
        labels={"index": "Run Index", "value": "Time (s)"},
    )
    tile = grid.container(border=False, width=500)
    tile.plotly_chart(fig, width="stretch")


st.divider()


def force_refresh():
    get_commits.clear()


def clear_artifacts():
    get_commits.clear()
    get_pytest_results.clear()


with st.expander("Debug Info"):
    st.button("Force refresh", on_click=force_refresh)
    st.button("Clear all artifacts", on_click=clear_artifacts)
    st.write("Commits for the develop branch:")
    st.dataframe(
        {
            "Commit Hash": [
                f"https://github.com/streamlit/streamlit/commit/{hash}"
                for hash in commit_hashes
            ],
        },
        column_config={
            "Commit Hash": st.column_config.LinkColumn(
                display_text="https://github.com/streamlit/streamlit/commit/(.*)",
            )
        },
        hide_index=False,
    )
    st.write("Test Names:")
    st.dataframe(list(all_tests))
