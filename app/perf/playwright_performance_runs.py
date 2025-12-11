import concurrent.futures
from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from app.perf import (
    playwright_interpreting_results,
    playwright_metrics_explorer,
    playwright_writing_a_test,
)
from app.perf.utils.artifacts import get_artifact_results
from app.perf.utils.perf_github_artifacts import get_commit_hashes_for_branch_name
from app.perf.utils.help_text import get_help_text
from app.perf.utils.tab_nav import segmented_tabs
from app.perf.utils.test_diff_analyzer import (
    find_and_remove_outliers,
    process_test_results_directory,
)

TITLE = "Streamlit Performance - Playwright"

st.set_page_config(page_title=TITLE, layout="wide")

title_row = st.container(
    horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"
)
with title_row:
    st.title("🎭 Performance - Playwright")

tab = segmented_tabs(
    options=["Runs", "Interpret metrics", "Write a test", "Explorer"],
    key="playwright_tab",
    query_param="tab",
    default="Runs",
)

if tab != "Runs":
    if tab == "Interpret metrics":
        playwright_interpreting_results.render_interpreting_results()
    elif tab == "Write a test":
        playwright_writing_a_test.render_writing_a_test()
    elif tab == "Explorer":
        playwright_metrics_explorer.render_metrics_explorer()
    st.stop()

token = st.secrets["github"]["token"]

if token is None:
    st.error("No GitHub token provided")
    st.stop()


@st.cache_data
def get_commits(
    branch_name: str, token: str, until_date: Optional[str] = None, limit: int = 20
):
    return get_commit_hashes_for_branch_name(
        branch_name, limit=limit, until_date=until_date
    )


@st.cache_data
def get_everything_by_hash(hash: str):
    return get_artifact_results(hash, "playwright")


selected_test_param = st.query_params.get("test")
show_mean_line = st.query_params.get("show_mean_line", "True").lower() == "true"
show_boxplot = st.query_params.get("show_boxplot", "True").lower() == "true"
load_all_metrics = st.query_params.get("load_all_metrics", "False").lower() == "true"
y_domain_includes_zero = (
    st.query_params.get("y_domain_includes_zero", "True").lower() == "true"
)


def on_query_param_change():
    if "selected_test" in st.session_state:
        st.query_params.test = str(st.session_state.selected_test)
    if "show_mean_line" in st.session_state:
        st.query_params.show_mean_line = str(st.session_state.show_mean_line).lower()
    if "show_boxplot" in st.session_state:
        st.query_params.show_boxplot = str(st.session_state.show_boxplot).lower()
    if "load_all_metrics" in st.session_state:
        st.query_params.load_all_metrics = str(
            st.session_state.load_all_metrics
        ).lower()
    if "y_domain_includes_zero" in st.session_state:
        st.query_params.y_domain_includes_zero = str(
            st.session_state.y_domain_includes_zero
        ).lower()


all_tests: set[str] = set()

with st.container(width="content"):
    selected_date = st.date_input(
        "Show commits until date:",
        value=None,
        help="Select a date to show commits up until (leave empty for latest commits)",
    )

# Get the commits and process data first
commit_hashes = get_commits(
    "develop", token, until_date=selected_date.isoformat() if selected_date else None
)

directories: list[str] = []
timestamps: list[str] = []

# Download all the artifacts for the Playwright performance runs in parallel
with concurrent.futures.ThreadPoolExecutor() as executor:
    # Create futures with their corresponding indices and hashes
    future_mapping = {
        executor.submit(get_everything_by_hash, hash): (i, hash)
        for i, hash in enumerate(commit_hashes)
    }

    # Create a list to store results in correct order
    ordered_artifacts = []

    # Process futures as they complete
    for future in concurrent.futures.as_completed(future_mapping):
        idx, hash = future_mapping[future]
        directory, timestamp = future.result()

        if (
            directory == ""
            and timestamp == ""
            or directory is None
            or timestamp is None
        ):
            continue

        ordered_artifacts.append((idx, directory, timestamp, hash))

# Sort first by timestamp and maintain original order as secondary sort key
ordered_artifacts.sort(key=lambda x: (x[2], x[0]))
# Unpack sorted artifacts, discarding the index used for ordering
_, directories, timestamps, commit_hashes = (
    zip(*ordered_artifacts) if ordered_artifacts else ([], [], [], [])
)

all_tests = set()
all_metric_names = set()

processed_results = {}

for directory in directories:
    res = process_test_results_directory(directory, load_all_metrics)
    res = find_and_remove_outliers(res)

    processed_results[directory] = res

    for test_name in res.keys():
        all_tests.add(test_name)
        for metric_name in res[test_name].keys():
            all_metric_names.add(f"{test_name}.{metric_name}")

# Now set up the UI with the collected test names
sorted_all_tests = sorted(list(all_tests))
selected_test = (
    selected_test_param
    if selected_test_param in sorted_all_tests
    else (sorted_all_tests[0] if sorted_all_tests else "")
)

with st.container(width="content"):
    selected_test = st.selectbox(
        "Select a test:",
        sorted_all_tests,
        index=(
            sorted_all_tests.index(selected_test)
            if selected_test in sorted_all_tests
            else 0
        ),
        on_change=on_query_param_change,
        key="selected_test",
    )
    show_mean_line = st.checkbox(
        "Show Mean Line",
        key="show_mean_line",
        value=show_mean_line,
        on_change=on_query_param_change,
    )
    show_boxplot = st.checkbox(
        "Show Boxplot",
        key="show_boxplot",
        value=show_boxplot,
        on_change=on_query_param_change,
    )
    y_domain_includes_zero = st.checkbox(
        "Y-axis includes zero",
        key="y_domain_includes_zero",
        value=y_domain_includes_zero,
        help="Force the Y-axis to include zero",
        on_change=on_query_param_change,
    )
    load_all_metrics = st.checkbox(
        "Show all metrics",
        key="load_all_metrics",
        value=load_all_metrics,
        help="Shows all available metrics data. Many of these metrics might not be reliable or useful.",
        on_change=on_query_param_change,
    )


st.divider()


filtered_test_names = [
    test_name for test_name in all_metric_names if selected_test in test_name
]
filtered_test_names.sort(key=str.lower)

grid = st.container(horizontal=True, gap="medium")

for idx, metric_name in enumerate(filtered_test_names):
    data = []
    total_points = len(processed_results)
    for directory_idx, (directory, results) in enumerate(processed_results.items()):
        for test_name, tests in results.items():
            if metric_name in [f"{test_name}.{t}" for t in tests.keys()]:
                test_result = tests[metric_name.split(".")[1]]

                for point in test_result:
                    data.append(
                        {
                            "value": point,
                            "index": directory_idx,  # No change needed - index now naturally goes from oldest to newest
                            "timestamp": timestamps[directory_idx],
                            "commit_hash": commit_hashes[directory_idx][:7],
                        }
                    )

    if data:

        def format_metric_name(metric_name: str) -> str:
            substr_mapping = {
                "duration_ms": "total duration (ms)",
                "long_animation_frames": "Long animation frames",
            }

            for substr, replacement in substr_mapping.items():
                metric_name = metric_name.replace(substr, replacement)

            return metric_name.replace("__", " ").replace("_", " ")

        df = pd.DataFrame(data)
        metric_name = metric_name.split(".")[1]
        metric_help_text = get_help_text(metric_name)
        metric_name = format_metric_name(metric_name)

        scatter_fig = px.scatter(
            df,
            x="index",
            y="value",
            # title=metric_name,
            hover_data=[
                "timestamp",
                "commit_hash",
            ],  # Display commit hash in hover data
        )
        scatter_fig.update_traces(marker=dict(symbol="circle", opacity=0.6))
        mean_df = df.groupby("index").agg({"value": "mean"}).reset_index()

        if y_domain_includes_zero:
            data_min = min([min(df["value"]), 0])
            data_max = max(df["value"]) * 1.1
        else:
            data_min = min(df["value"])
            data_max = max(df["value"])

        # Add padding in both directions for better visualization
        range_padding = (
            (data_max - data_min) * 0.1 if data_max > data_min else data_max * 0.1
        )

        y_min = data_min - range_padding
        y_max = data_max + range_padding

        scatter_fig.update_layout(yaxis_range=[y_min, y_max])

        if show_mean_line:
            line_fig = px.line(mean_df, x="index", y="value")

            for trace in line_fig.data:
                scatter_fig.add_trace(trace)

        if show_boxplot:
            boxplot_fig = px.box(df, x="index", y="value", title=metric_name)
            for trace in boxplot_fig.data:
                scatter_fig.add_trace(trace)

        # Use a fixed-width tile so the horizontal flex container can lay out
        # multiple charts per row and wrap naturally on smaller screens.
        tile = grid.container(border=False, width=500)
        tile.markdown(
            f"**{metric_name}**",
            # help=metric_help_text,
        )
        tile.plotly_chart(scatter_fig, key=metric_name, width="stretch")


st.divider()


def force_refresh():
    get_commits.clear()


with st.expander("Debug Info"):
    st.button("Force refresh", on_click=force_refresh)
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
    st.dataframe(list(all_metric_names))
