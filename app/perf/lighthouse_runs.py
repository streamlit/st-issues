import concurrent.futures
import operator
from datetime import datetime

import pandas as pd
import streamlit as st

from app.perf import (
    lighthouse_interpreting_results,
    lighthouse_writing_a_test,
)
from app.perf.utils.artifacts import get_artifact_results
from app.perf.utils.commit_details import (
    render_selected_commit_sidebar,
    reset_selection_on_page_change,
    update_selected_commit,
)
from app.perf.utils.perf_github_artifacts import (
    append_to_performance_scores,
    get_commit_hashes_for_branch_name,
)
from app.perf.utils.tab_nav import segmented_tabs
from app.utils import echarts as ec

TITLE = "Lighthouse performance"

st.set_page_config(page_title=TITLE)

title_row = st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center")
with title_row:
    st.title(":material/lightbulb: Lighthouse performance")

tab = segmented_tabs(
    options=["Runs", "Interpret metrics", "Write a test"],
    key="lighthouse_tab",
    query_param="tab",
    default="Runs",
)

if tab != "Runs":
    if tab == "Interpret metrics":
        lighthouse_interpreting_results.render_interpreting_results()
    elif tab == "Write a test":
        lighthouse_writing_a_test.render_writing_a_test()
    st.stop()

token = st.secrets["github"]["token"]

if token is None:
    st.error("No GitHub token provided")
    st.stop()

reset_selection_on_page_change("perf_lighthouse_runs")
render_selected_commit_sidebar()


@st.cache_data(ttl=60 * 60 * 12, refresh_mode="background")
def get_commits(branch_name: str, limit: int = 20) -> list[str]:
    return get_commit_hashes_for_branch_name(branch_name, limit=limit)


@st.cache_data(ttl=60 * 60 * 12, refresh_mode="background")
def get_lighthouse_results(commit_hash: str) -> tuple:
    return get_artifact_results(commit_hash, "lighthouse")


commit_hashes = get_commits("develop")

directories: list[str] = []
run_results: list[tuple[str, str, dict[str, float]]] = []

# Download all the artifacts for the performance runs in parallel
with concurrent.futures.ThreadPoolExecutor() as executor:
    future_mapping = {
        executor.submit(get_lighthouse_results, commit_hash): commit_hash for commit_hash in commit_hashes
    }
    for future in concurrent.futures.as_completed(future_mapping):
        commit_hash = future_mapping[future]
        scores, timestamp = future.result()

        if not scores or not timestamp:
            continue

        run_results.append((timestamp, commit_hash, scores))

# Guard: no data found
if not run_results:
    st.info("No Lighthouse artifacts found for the selected commits.")
    st.stop()

# Sort scores and timestamps based on timestamps
sorted_runs = sorted(run_results, key=operator.itemgetter(0))
timestamps_sorted, commit_hashes_sorted, scores_by_run_sorted = zip(*sorted_runs, strict=False)
commit_hash_by_timestamp = {timestamp: commit_hash for timestamp, commit_hash, _scores in sorted_runs}

performance_scores: dict[str, dict] = {}

for idx, scores in enumerate(scores_by_run_sorted):
    for app_name, score in scores.items():
        append_to_performance_scores(performance_scores, timestamps_sorted[idx], app_name, score)


# Convert performance_scores to a DataFrame
data = []
for datetime_str, apps in performance_scores.items():
    parsed_datetime = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ")
    commit_hash = commit_hash_by_timestamp.get(datetime_str, "")
    for app_name, score in apps.items():
        if score is None:
            continue

        data.append(
            {
                "datetime": parsed_datetime,
                "app_name": app_name,
                "score": score * 100,
                "commit_hash": commit_hash[:7] if commit_hash else "",
                "commit_sha_full": commit_hash,
            }
        )

df = pd.DataFrame(data)

if df.empty:
    st.info("No Lighthouse score data found in the downloaded artifacts.")
    st.stop()

# Add an index to the DataFrame
df["index"] = df.groupby("app_name").cumcount()

# Sort the DataFrame by index to ensure deterministic rolling mean calculation
df = df.sort_values(by=["app_name", "index"])

# Calculate rolling mean
df["rolling_mean"] = df.groupby("app_name")["score"].transform(lambda x: x.rolling(window=5, min_periods=1).mean())

df["score"] = df["score"].round(1)
df["rolling_mean"] = df["rolling_mean"].round(1)
df["date"] = df["datetime"].dt.strftime("%Y-%m-%d %H:%M")

app_frames = [app_df.reset_index(drop=True) for _app_name, app_df in df.groupby("app_name", sort=True)]
series: list[dict] = []
series_frames: list[pd.DataFrame] = []
for dataset_index, app_df in enumerate(app_frames):
    app_name = str(app_df["app_name"].iloc[0])
    series.extend(
        [
            {
                "type": "line",
                "name": app_name,
                "datasetIndex": dataset_index,
                "encode": {"x": "index", "y": "rolling_mean"},
                "tooltip": ec.item_tooltip(
                    ["rolling_mean", "date", "commit_hash"], labels={"rolling_mean": "Rolling mean"}
                ),
                "showSymbol": False,
            },
            {
                "type": "scatter",
                "name": app_name,
                "datasetIndex": dataset_index,
                "encode": {"x": "index", "y": "score"},
                "tooltip": ec.item_tooltip(["score", "date", "commit_hash"]),
                "selectedMode": "single",
                "symbolSize": 7,
            },
        ]
    )
    series_frames.extend([app_df, app_df])

selection = st.echarts_chart(
    {
        "title": {"text": "Lighthouse scores over time"},
        "legend": {"type": "scroll", "top": 32},
        "grid": {"top": 72},
        "tooltip": {"trigger": "item"},
        "dataset": [{"source": app_df} for app_df in app_frames],
        "xAxis": {"type": "value", "name": "Run", "minInterval": 1},
        "yAxis": {"type": "value", "min": 0, "max": 100, "name": "Score"},
        "series": series,
    },
    key="lighthouse-runs",
    on_select="rerun",
    alt="Lighthouse scores per app over recent develop runs, with five-run rolling means",
)
selected_shas = [
    series_frames[group["series_index"]]["commit_sha_full"].iloc[row]
    for group in selection.selection.selected
    for row in group["data_indices"]
]
update_selected_commit(selected_shas, selection_key="lighthouse-runs")

with st.expander("Raw Data"):
    st.dataframe(df)
