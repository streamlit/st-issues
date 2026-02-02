import concurrent.futures
import operator

import pandas as pd
import plotly.express as px
import streamlit as st

from app.perf import (
    pytest_interpreting_results,
    pytest_writing_a_test,
)
from app.perf.utils.artifacts import get_artifact_results
from app.perf.utils.commit_details import (
    render_selected_commit_sidebar,
    reset_selection_on_page_change,
    update_selected_commit_from_selection,
)
from app.perf.utils.perf_github_artifacts import get_commit_hashes_for_branch_name
from app.perf.utils.pytest_types import BenchmarkStats, OutputJson
from app.perf.utils.tab_nav import segmented_tabs

TITLE = "Streamlit Performance - Pytest"

st.set_page_config(page_title=TITLE, layout="wide")

title_row = st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center")
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

reset_selection_on_page_change("perf_pytest_runs")
render_selected_commit_sidebar()


@st.cache_data(ttl=60 * 60 * 12)
def get_commits(branch_name: str, limit: int = 50) -> list[str]:
    return get_commit_hashes_for_branch_name(branch_name, limit=limit)


@st.cache_data(ttl=60 * 60 * 12)
def get_pytest_results(commit_hash: str) -> tuple:
    return get_artifact_results(commit_hash, "pytest")


commit_hashes = get_commits("develop")


directories: list[str] = []
run_results: list[tuple[str, str, OutputJson]] = []

# Download all the artifacts for the performance runs in parallel
with concurrent.futures.ThreadPoolExecutor() as executor:
    future_mapping = {executor.submit(get_pytest_results, commit_hash): commit_hash for commit_hash in commit_hashes}
    for future in concurrent.futures.as_completed(future_mapping):
        commit_hash = future_mapping[future]
        results, timestamp = future.result()

        if not results or not timestamp:
            continue

        run_results.append((timestamp, commit_hash, results))

# Guard: no data found
if not run_results:
    st.info("No Pytest benchmark artifacts found for the selected commits.")
    st.stop()

# Sort results and timestamps based on timestamps
sorted_runs = sorted(run_results, key=operator.itemgetter(0))
timestamps_sorted, commit_hashes_sorted, results_by_run = zip(*sorted_runs, strict=False)


all_tests_set: set[str] = set()
processed_results: dict[str, BenchmarkStats] = {}
benchmark_data: list[dict] = []

for run_index, (results, timestamp, commit_hash) in enumerate(
    zip(results_by_run, timestamps_sorted, commit_hashes_sorted, strict=False)
):
    for test in results["benchmarks"]:
        all_tests_set.add(test["name"])

        if test["name"] not in processed_results:
            processed_results[test["name"]] = test["stats"]

        benchmark_data.append(
            {
                "test_name": test["name"],
                "run_index": run_index,
                "timestamp": timestamp,
                "commit_hash": commit_hash[:7],
                "commit_sha_full": commit_hash,
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

all_tests = sorted(all_tests_set)

for test_name in all_tests:
    test_df = df[df["test_name"] == test_name].reset_index(drop=True)
    fig = px.scatter(
        test_df,
        x="run_index",
        y="median",
        title=test_name,
        labels={"run_index": "Run Index", "median": "Time (s)"},
        hover_data=["timestamp", "commit_hash"],
        custom_data=["commit_sha_full"],
    )
    fig.update_traces(marker=dict(symbol="circle", opacity=0.6))
    fig.update_layout(clickmode="event+select")

    box_fig = px.box(
        test_df,
        x="run_index",
        y=["min", "q1", "median", "q3", "max"],
        points=None,
        custom_data=["commit_sha_full"],
    )
    box_fig.update_traces(showlegend=False)
    for trace in box_fig.data:
        fig.add_trace(trace)

    box_traces: list = []
    line_traces: list = []
    marker_traces: list = []
    other_traces: list = []
    for trace in fig.data:
        mode = getattr(trace, "mode", "") or ""
        if trace.type == "box":
            box_traces.append(trace)
        elif trace.type == "scatter" and "markers" in mode:
            marker_traces.append(trace)
        elif trace.type == "scatter" and "lines" in mode:
            line_traces.append(trace)
        else:
            other_traces.append(trace)
    fig.data = tuple(box_traces + line_traces + other_traces + marker_traces)

    tile = grid.container(border=False, width=500)
    selection = tile.plotly_chart(
        fig,
        width="stretch",
        key=f"pytest-{test_name}",
        on_select="rerun",
        selection_mode="points",
    )
    update_selected_commit_from_selection(selection, selection_key=f"pytest-{test_name}")


st.divider()


def force_refresh() -> None:
    get_commits.clear()


def clear_artifacts() -> None:
    get_commits.clear()
    get_pytest_results.clear()


with st.expander("Debug Info"):
    st.button("Force refresh", on_click=force_refresh)
    st.button("Clear all artifacts", on_click=clear_artifacts)
    st.write("Commits for the develop branch:")
    st.dataframe(
        {
            "Commit Hash": [f"https://github.com/streamlit/streamlit/commit/{h}" for h in commit_hashes],
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
