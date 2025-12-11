import streamlit as st

from app.perf.utils.perf_github_artifacts import get_workflow_run_id
from app.utils.github_utils import get_all_github_prs

TITLE = "Streamlit Performance - Open PRs"

st.set_page_config(page_title=TITLE)

st.header(TITLE)

token = st.secrets["github"]["token"]

if token is None:
    st.error("No GitHub token provided")
    st.stop()


@st.cache_data
def get_all_prs():
    prs = get_all_github_prs(state="open")
    return [
        pr
        for pr in prs
        if any(lbl.get("name") == "perf:lighthouse" for lbl in pr.get("labels", []))
    ]


all_prs = get_all_prs()


@st.cache_data
def cached_get_workflow_run_id(pr_ref):
    return get_workflow_run_id(pr_ref, "Performance - Lighthouse")


for pr in all_prs:
    pr_title = pr["title"]
    pr_url = pr["html_url"]
    pr_ref = pr["head"]["ref"]
    st.write(f"PR: {pr_title} ({pr_url})")

    run_id = cached_get_workflow_run_id(pr_ref)
    st.write(f"Run ID: {run_id}")
    st.write("---")
