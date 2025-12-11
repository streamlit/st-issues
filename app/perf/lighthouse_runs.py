import concurrent.futures
from datetime import datetime
from typing import List, Optional

import altair as alt
import pandas as pd
import streamlit as st

from app.perf import lighthouse_interpreting_results, lighthouse_writing_a_test
from app.perf.utils.artifacts import get_artifact_results
from app.perf.utils.perf_github_artifacts import (
    get_commit_hashes_for_branch_name,
    read_json_files,
)
from app.perf.utils.tab_nav import segmented_tabs

TITLE = "Streamlit Performance - Lighthouse"

st.set_page_config(page_title=TITLE)

title_row = st.container(
    horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"
)
with title_row:
    st.title("💡 Performance - Lighthouse")

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


@st.cache_data
def get_commits(branch_name: str, token: str, limit: int = 20):
    return get_commit_hashes_for_branch_name(branch_name, limit=limit)


@st.cache_data
def get_lighthouse_results(hash: str) -> Optional[str]:
    return get_artifact_results(hash, "lighthouse")


commit_hashes = get_commits("develop", token)

directories: List[str] = []
timestamps = []

# Download all the artifacts for the performance runs in parallel
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [
        executor.submit(get_lighthouse_results, commit_hash)
        for commit_hash in commit_hashes
    ]
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

performance_scores = {}

for idx, directory in enumerate(directories):
    # Process the artifact directory to extract performance scores
    read_json_files(performance_scores, timestamps[idx], directory)


# Convert performance_scores to a DataFrame
data = []
for datetime_str, apps in performance_scores.items():
    parsed_datetime = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ")
    for app_name, score in apps.items():
        if score is None:
            continue

        data.append(
            {
                "datetime": parsed_datetime,
                "app_name": app_name,
                "score": score * 100,
            }
        )

df = pd.DataFrame(data)

# Add an index to the DataFrame
df["index"] = df.groupby("app_name").cumcount()

# Sort the DataFrame by index to ensure deterministic rolling mean calculation
df = df.sort_values(by=["app_name", "index"])

# Calculate rolling mean
df["rolling_mean"] = df.groupby("app_name")["score"].transform(
    lambda x: x.rolling(window=5, min_periods=1).mean()
)

chart = (
    alt.Chart(df)
    .mark_point()
    .encode(
        x=alt.X(
            "index:Q",
            # Ensure x-axis shows only integers
            axis=alt.Axis(format="d"),
        ),
        y=alt.Y("score:Q", scale=alt.Scale(domain=[0, 100])),
        color="app_name:N",
        tooltip=["datetime:T", "score:Q", "app_name:N"],
    )
    .properties(title="Lighthouse Scores Over Time")
)

rolling_mean_line = (
    alt.Chart(df)
    .mark_line()
    .encode(
        x=alt.X(
            "index:Q",
            # Ensure x-axis shows only integers
            axis=alt.Axis(format="d"),
        ),
        y=alt.Y("rolling_mean:Q"),
        color="app_name:N",
        tooltip=["datetime:T", "rolling_mean:Q", "app_name:N"],
    )
)

st.altair_chart(chart + rolling_mean_line, width="stretch")

with st.expander("Raw Data"):
    st.dataframe(df)
