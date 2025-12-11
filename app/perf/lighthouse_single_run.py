from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

from app.perf.utils.perf_github_artifacts import process_artifact
from app.utils.github_utils import fetch_artifacts

TITLE = "Streamlit Performance - Single Lighthouse Run"


st.set_page_config(page_title=TITLE)

token = st.secrets["github"]["token"]

if token is None:
    st.error("No GitHub token provided")
    st.stop()


# Add run_id into st.session_state if it doesn't yet exist
if "run_id" not in st.session_state:
    st.session_state.run_id = None


st.header(TITLE)

with st.form(key="github_form"):
    run_id = st.text_input("GitHub Run ID", "12704582295")

    submitted = st.form_submit_button("Submit")
    if submitted:
        st.session_state.run_id = run_id


if st.session_state.run_id is None or st.session_state.run_id == "":
    st.write("No GitHub Run ID provided")
    st.stop()


@st.cache_data(ttl=60 * 60 * 12)
def get_and_extract_performance_for_run(run_id):
    artifacts = {"artifacts": fetch_artifacts(int(run_id))}

    performance_scores = {}

    for artifact in artifacts["artifacts"]:
        if artifact["name"].startswith("performance_lighthouse"):
            process_artifact(performance_scores, artifact)

    return performance_scores


performance_scores = get_and_extract_performance_for_run(st.session_state.run_id)

if not performance_scores:
    st.info("No Lighthouse artifacts found for this run ID.")
    st.stop()


# Convert performance_scores to a DataFrame
data = []
for datetime_str, apps in performance_scores.items():
    parsed_datetime = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ")
    for app_name, score in apps.items():
        data.append(
            {
                "datetime": parsed_datetime,
                "app_name": app_name,
                "score": score * 100,
            }
        )

df = pd.DataFrame(data)


chart = (
    alt.Chart(df)
    .mark_point()
    .encode(
        x="datetime:T",
        y=alt.Y("score:Q", scale=alt.Scale(domain=[0, 100])),
        color="app_name:N",
    )
    .properties(title="Lighthouse Scores Over Time")
)

st.altair_chart(chart, width="stretch")


with st.expander("Raw Data"):
    st.dataframe(df)
