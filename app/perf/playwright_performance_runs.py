import concurrent.futures
import operator

import pandas as pd
import plotly.express as px
import streamlit as st

from app.perf import (
    playwright_interpreting_results,
    playwright_metrics_explorer,
    playwright_writing_a_test,
)
from app.perf.utils.artifacts import get_artifact_results
from app.perf.utils.commit_details import (
    render_selected_commit_sidebar,
    reset_selection_on_page_change,
    update_selected_commit_from_selection,
)
from app.perf.utils.help_text import get_help_text
from app.perf.utils.perf_github_artifacts import (
    get_commit_hashes_for_branch_name,
)
from app.perf.utils.tab_nav import segmented_tabs
from app.perf.utils.test_diff_analyzer import (
    find_and_remove_outliers,
)

TITLE = "Streamlit Performance - Playwright"

st.set_page_config(page_title=TITLE, layout="wide")

title_row = st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center")
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

reset_selection_on_page_change("perf_playwright_runs")
render_selected_commit_sidebar()


@st.cache_data(ttl=60 * 60 * 12)
def get_commits(branch_name: str, until_date: str | None = None, limit: int = 50) -> list[str]:
    return get_commit_hashes_for_branch_name(branch_name, limit=limit, until_date=until_date)


@st.cache_data(ttl=60 * 60 * 12)
def get_everything_by_hash(commit_hash: str, load_all_metrics: bool) -> tuple:
    return get_artifact_results(commit_hash, "playwright", load_all_metrics=load_all_metrics)


selected_test_param = st.query_params.get("test")
show_mean_line = st.query_params.get("show_mean_line", "True").lower() == "true"
show_boxplot = st.query_params.get("show_boxplot", "True").lower() == "true"
load_all_metrics = st.query_params.get("load_all_metrics", "False").lower() == "true"
y_domain_includes_zero = st.query_params.get("y_domain_includes_zero", "True").lower() == "true"


def on_query_param_change() -> None:
    if "selected_test" in st.session_state:
        st.query_params.test = str(st.session_state.selected_test)
    if "show_mean_line" in st.session_state:
        st.query_params.show_mean_line = str(st.session_state.show_mean_line).lower()
    if "show_boxplot" in st.session_state:
        st.query_params.show_boxplot = str(st.session_state.show_boxplot).lower()
    if "load_all_metrics" in st.session_state:
        st.query_params.load_all_metrics = str(st.session_state.load_all_metrics).lower()
    if "y_domain_includes_zero" in st.session_state:
        st.query_params.y_domain_includes_zero = str(st.session_state.y_domain_includes_zero).lower()


with st.container(width="content"):
    selected_date = st.date_input(
        "Show commits until date:",
        value=None,
        help="Select a date to show commits up until (leave empty for latest commits)",
    )

# Get the commits and process data first
initial_commit_hashes = get_commits("develop", until_date=selected_date.isoformat() if selected_date else None)

run_results_list: list[dict] = []
timestamps_list: list[str] = []

# Download all the artifacts for the Playwright performance runs in parallel
with concurrent.futures.ThreadPoolExecutor() as executor:
    # Create futures with their corresponding indices and hashes
    future_mapping = {
        executor.submit(get_everything_by_hash, h, load_all_metrics): (i, h)
        for i, h in enumerate(initial_commit_hashes)
    }

    # Create a list to store results in correct order
    ordered_artifacts = []

    # Process futures as they complete
    for future in concurrent.futures.as_completed(future_mapping):
        idx, h = future_mapping[future]
        results, timestamp = future.result()

        if (not results and not timestamp) or results is None or timestamp is None:
            continue

        ordered_artifacts.append((idx, results, timestamp, h))

# Sort first by timestamp and maintain original order as secondary sort key
ordered_artifacts.sort(key=operator.itemgetter(2, 0))
# Unpack sorted artifacts, discarding the index used for ordering
run_results_tuple: tuple = ()
timestamps_tuple: tuple = ()
commit_hashes_tuple: tuple = ()
if ordered_artifacts:
    _, run_results_tuple, timestamps_tuple, commit_hashes_tuple = zip(*ordered_artifacts, strict=False)

all_tests: set[str] = set()
all_metric_names: set[str] = set()

processed_results: dict[str, dict] = {}

for commit_hash, run_res in zip(commit_hashes_tuple, run_results_tuple, strict=False):
    processed_run = find_and_remove_outliers(run_res)
    processed_results[commit_hash] = processed_run

    for test_name in processed_run:
        all_tests.add(test_name)
        all_metric_names.update(f"{test_name}.{metric_name}" for metric_name in processed_run[test_name])

# Now set up the UI with the collected test names
sorted_all_tests = sorted(all_tests)
selected_test = (
    selected_test_param
    if selected_test_param in sorted_all_tests
    else (sorted_all_tests[0] if sorted_all_tests else "")
)

with st.container(width="content"):
    selected_test = st.selectbox(
        "Select a test:",
        sorted_all_tests,
        index=(sorted_all_tests.index(selected_test) if selected_test in sorted_all_tests else 0),
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


filtered_test_names = [test_name for test_name in all_metric_names if selected_test in test_name]
filtered_test_names.sort(key=str.lower)

grid = st.container(horizontal=True, gap="medium")

for metric_name in filtered_test_names:
    data: list[dict] = []
    total_points = len(processed_results)
    for directory_idx, (_commit_key, results) in enumerate(processed_results.items()):
        for test_name, tests in results.items():
            if metric_name in [f"{test_name}.{t}" for t in tests]:
                metric_key = metric_name.split(".")[1]
                test_result = tests[metric_key]

                data.extend(
                    {
                        "value": point,
                        "index": directory_idx,  # No change needed - index now naturally goes from oldest to newest
                        "timestamp": timestamps_tuple[directory_idx],
                        "commit_hash": commit_hashes_tuple[directory_idx][:7],
                        "commit_sha_full": commit_hashes_tuple[directory_idx],
                    }
                    for point in test_result
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
        short_metric_name = metric_name.split(".")[1]
        metric_help_text = get_help_text(short_metric_name)
        display_metric_name = format_metric_name(short_metric_name)

        scatter_fig = px.scatter(
            df,
            x="index",
            y="value",
            # title=metric_name,
            hover_data=[
                "timestamp",
                "commit_hash",
            ],  # Display commit hash in hover data
            custom_data=["commit_sha_full"],
        )
        scatter_fig.update_traces(marker=dict(symbol="circle", opacity=0.6))
        mean_df = df.groupby("index").agg({"value": "mean", "commit_sha_full": "first"}).reset_index()

        if y_domain_includes_zero:
            data_min = min([min(df["value"]), 0])
            data_max = max(df["value"]) * 1.1
        else:
            data_min = min(df["value"])
            data_max = max(df["value"])

        # Add padding in both directions for better visualization
        range_padding = (data_max - data_min) * 0.1 if data_max > data_min else data_max * 0.1

        y_min = data_min - range_padding
        y_max = data_max + range_padding

        scatter_fig.update_layout(yaxis_range=[y_min, y_max], clickmode="event+select")

        if show_mean_line:
            line_fig = px.line(mean_df, x="index", y="value", custom_data=["commit_sha_full"])

            for trace in line_fig.data:
                scatter_fig.add_trace(trace)

        if show_boxplot:
            boxplot_fig = px.box(df, x="index", y="value", title=display_metric_name, custom_data=["commit_sha_full"])
            for trace in boxplot_fig.data:
                scatter_fig.add_trace(trace)

        box_traces: list = []
        line_traces: list = []
        marker_traces: list = []
        other_traces: list = []
        for trace in scatter_fig.data:
            mode = getattr(trace, "mode", "") or ""
            if trace.type == "box":
                box_traces.append(trace)
            elif trace.type == "scatter" and "markers" in mode:
                marker_traces.append(trace)
            elif trace.type == "scatter" and "lines" in mode:
                line_traces.append(trace)
            else:
                other_traces.append(trace)
        scatter_fig.data = tuple(box_traces + line_traces + other_traces + marker_traces)

        # Use a fixed-width tile so the horizontal flex container can lay out
        # multiple charts per row and wrap naturally on smaller screens.
        tile = grid.container(border=False, width=500)
        tile.markdown(
            f"**{display_metric_name}**",
            # help=metric_help_text,
        )
        selection = tile.plotly_chart(
            scatter_fig,
            key=f"playwright-{metric_name}",
            width="stretch",
            on_select="rerun",
            selection_mode="points",
        )
        update_selected_commit_from_selection(selection, selection_key=f"playwright-{metric_name}")


st.divider()


def force_refresh() -> None:
    get_commits.clear()


with st.expander("Debug Info"):
    st.button("Force refresh", on_click=force_refresh)
    st.write("Commits for the develop branch:")
    st.dataframe(
        {
            "Commit Hash": [f"https://github.com/streamlit/streamlit/commit/{h}" for h in commit_hashes_tuple],
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
