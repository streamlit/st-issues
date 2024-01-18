import json
import pathlib
import re
import urllib.request
from typing import List, Optional
from urllib.parse import quote

import pandas as pd
import streamlit as st

DEFAULT_ISSUES_FOLDER = "issues"
PATH_OF_SCRIPT = pathlib.Path(__file__).parent.resolve()
PATH_TO_ISSUES = (
    pathlib.Path(PATH_OF_SCRIPT).parent.joinpath(DEFAULT_ISSUES_FOLDER).resolve()
)

st.set_page_config(
    page_title="Open Issues",
    page_icon="🗃",
    initial_sidebar_state="collapsed",
)


# Paginate through all open issues in the streamlit/streamlit repo
# and return them all as a list of dicts.
@st.cache_data(ttl=60 * 60 * 6)  # cache for 6 hours
def get_all_github_issues():
    issues = []
    page = 1
    while True:
        try:
            with urllib.request.urlopen(
                f"https://api.github.com/repos/streamlit/streamlit/issues?state=open&per_page=100&page={page}"
            ) as response:
                if response:
                    data = json.loads(response.read())
                    if not data:
                        break
                    issues.extend(data)
                    page += 1
        except Exception as ex:
            print(ex, flush=True)
            break
    return issues


# Ignore Pull Requests
all_issues = [issue for issue in get_all_github_issues() if "pull_request" not in issue]
all_labels = set()

for issue in all_issues:
    for label in issue["labels"]:
        all_labels.add(label["name"])


def initial_query_params() -> dict:
    """
    When page is first loaded, or if current params are empty, sync url params to
    session state. Afterwards, just return local copy.
    """
    if (
        "initial_query_params" not in st.session_state
        or not st.session_state["initial_query_params"]
    ):
        st.session_state["initial_query_params"] = st.experimental_get_query_params()
    return st.session_state["initial_query_params"]


default_filters = []
query_params = initial_query_params()
if "label" in query_params:
    default_filters = query_params["label"]

filter_labels = st.sidebar.multiselect(
    "Filter by label", list(all_labels), default=default_filters
)
filter_missing_labels = st.sidebar.checkbox(
    "Filter issues that require feature labels", value=False
)

print("Show issues with labels:", filter_labels, flush=True)

st.experimental_set_query_params(label=filter_labels)

filtered_issues = []
for issue in all_issues:
    filtered_out = False
    issue_labels: List[str] = [label["name"] for label in issue["labels"]]
    if filter_missing_labels:
        filtered_out = False
        for label in issue_labels:
            if label.startswith("feature:") or label.startswith("area:"):
                filtered_out = True
                break

    for filter_label in filter_labels:
        if filter_label not in issue_labels:
            filtered_out = True

    if not filtered_out:
        filtered_issues.append(issue)


link_qs_labels = "+".join([quote("label:" + label) for label in filter_labels])
link = f"https://github.com/streamlit/streamlit/issues?q={quote('is:open')}+{quote('is:issue')}+{link_qs_labels}"

st.markdown("")  # Add some space to prevent issue in embedded mode
st.caption(
    f"**{len(filtered_issues)} issues** found based on the selected filters. [View on GitHub ↗️]({link})"
)


REACTION_EMOJI = {
    "+1": "👍",
    "-1": "👎",
    "confused": "😕",
    "eyes": "👀",
    "heart": "❤️",
    "hooray": "🎉",
    "laugh": "😄",
    "rocket": "🚀",
}


def reactions_to_str(reactions):
    return " ".join(
        [
            f"{reactions[name]} {emoji}"
            for name, emoji in REACTION_EMOJI.items()
            if reactions[name] > 0
        ]
    )


def labels_to_type(labels: List[str]):
    if "type:enhancement" in labels:
        return "✨"
    elif "type:bug" in labels:
        return "🚨"
    else:
        return "❓"


def get_reproducible_example(issue_number: int):
    issue_folder_name = f"gh-{issue_number}"
    if PATH_TO_ISSUES.joinpath(issue_folder_name).is_dir():
        return "/?issue=" + issue_folder_name
    return None


def get_view_count(issue_number: int) -> Optional[int]:
    if issue_number < 7188:
        # We only added the view count badge after issue 7188
        return None
    url = f"https://hits.seeyoufarm.com/api/count/keep/badge.svg?url=https://github.com/streamlit/streamlit/issues/{issue_number}"
    # Load the SVG and extract the view count
    try:
        with urllib.request.urlopen(url) as response:
            if not response or response.status != 200:
                return None

            data = response.read().decode("utf-8")

            if match := re.search(r"([0-9]+) / ([0-9]+)", data):
                return int(match.group(2))
        return None
    except Exception:
        return None


@st.cache_data(ttl=60 * 60 * 6)  # cache for 6 hours
def get_view_counts(issue_numbers_series: pd.Series) -> pd.Series:
    return issue_numbers_series.map(get_view_count)


df = pd.DataFrame.from_dict(filtered_issues)
if df.empty:
    st.markdown("No issues found")
else:
    df["labels"] = df["labels"].map(
        lambda x: [label["name"] if label else "" for label in x]
    )
    df["type"] = df["labels"].map(labels_to_type)
    df["reproducible_example"] = df["number"].map(get_reproducible_example)
    df["title"] = df["type"] + df["title"]
    df["reaction_types"] = df["reactions"].map(reactions_to_str)
    df["total_reactions"] = (
        df["reactions"].map(lambda x: x["total_count"]) + df["comments"]
    )
    df["author_avatar"] = df["user"].map(lambda x: x["avatar_url"])
    df["assignee_avatar"] = df["assignee"].map(lambda x: x["avatar_url"] if x else None)
    df["views"] = get_view_counts(df["number"])
    df = df.sort_values(by=["total_reactions", "updated_at"], ascending=[False, False])
    st.dataframe(
        df[
            [
                "title",
                "total_reactions",
                "author_avatar",
                "updated_at",
                "created_at",
                "html_url",
                "reaction_types",
                "comments",
                "views",
                "assignee_avatar",
                "labels",
                "reproducible_example",
                # "author_association",
                "state",
            ]
        ],
        column_config={
            "title": st.column_config.TextColumn("Title", width=300),
            "type": "Type",
            "updated_at": st.column_config.DatetimeColumn(
                "Last Updated", format="distance"
            ),
            "created_at": st.column_config.DatetimeColumn(
                "Created at", format="distance"
            ),
            "author_avatar": st.column_config.ImageColumn("Author"),
            "total_reactions": st.column_config.NumberColumn(
                "Reactions", format="%d 🫶", help="Total number of reactions"
            ),
            "assignee_avatar": st.column_config.ImageColumn("Assignee"),
            "reaction_types": "Reactions Types",
            "labels": "Labels",
            "state": "State",
            "comments": st.column_config.NumberColumn("Comments", format="%d 💬"),
            "html_url": st.column_config.LinkColumn("Url", display_text="Open Issue"),
            "reproducible_example": st.column_config.LinkColumn(
                "Reproducible Example", width="medium"
            ),
            "views": st.column_config.NumberColumn("Views", format="%d 👁️", width=100),
        },
        hide_index=True,
    )
