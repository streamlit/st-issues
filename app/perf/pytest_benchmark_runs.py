import concurrent.futures
import json
from pathlib import Path
from typing import List, Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from app.perf.utils.artifacts import get_artifact_results
from app.perf.utils.github import (
    get_commit_hashes_for_branch_name,
    remove_artifact_directory,
)
from app.perf.utils.pytest_types import OutputJson

TITLE = "Streamlit Performance - Pytest Benchmark Runs"

st.set_page_config(page_title=TITLE, layout="wide")

st.header(TITLE)

token = st.secrets["github"]["token"]

if token is None:
    st.error("No GitHub token provided")
    st.stop()


@st.cache_data
def get_commits(branch_name: str, token: str, limit: int = 20):
    return get_commit_hashes_for_branch_name(branch_name, token=token, limit=limit)


@st.cache_data
def get_pytest_results(hash: str) -> Optional[str]:
    return get_artifact_results(hash, token, "pytest")


commit_hashes = get_commits("develop", token)


directories: List[str] = []
timestamps = []

# Download all the artifacts for the performance runs in parallel
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(get_pytest_results, run_id) for run_id in commit_hashes]
    for future in concurrent.futures.as_completed(futures):
        result = future.result()

        if result is None:
            continue

        directory, timestamp = result

        if directory is None:
            continue

        directories.append(directory)
        timestamps.append(timestamp)

# Sort directories and timestamps based on timestamps
sorted_directories_timestamps = sorted(zip(directories, timestamps), key=lambda x: x[1])
directories, timestamps = zip(*sorted_directories_timestamps)


all_tests = set()
processed_results = {}
benchmark_data = []

for directory in directories:
    # Pytest-benchmark stores results in a file that is named
    # <ID>_<hash>_<timestamp>.json. Since we don't have control over the name of
    # it, but we know there is only 1 file in the directory, we read the first
    # json file in the directory
    json_file = next(
        (f for f in Path(directory).iterdir() if f.suffix == ".json"), None
    )

    with open(json_file) as f:
        results: OutputJson = json.load(f)

        for test in results["benchmarks"]:
            all_tests.add(test["name"])

            if test["name"] not in processed_results:
                processed_results[test["name"]] = test["stats"]

            benchmark_data.append(
                {
                    "test_name": test["name"],
                    "directory": directory,
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
    remove_artifact_directory()
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
