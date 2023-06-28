import json
import os
import pathlib
import platform
import re
import urllib.request
from typing import Union

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Streamlit Issue", page_icon="🚧")
st.title("🚧 Streamlit Issues")

st.caption(
    f"""
A collection of Streamlit apps to replicate issues and bugs. Add your issue script [here](https://github.com/streamlit/st-issues).

Running with Python {platform.python_version()} and Streamlit {st.__version__}.
"""
)
DEFAULT_SELECTION = ""
DEFAULT_SCRIPT_NAME = "app.py"
DEFAULT_ISSUES_FOLDER = "issues"


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


path_of_script = pathlib.Path(__file__).parent.resolve()
path_to_issues = pathlib.Path(path_of_script).joinpath(DEFAULT_ISSUES_FOLDER).resolve()

issues = []
for issue_folder in os.listdir(path_to_issues):
    issue_folder_path = path_to_issues.joinpath(issue_folder).resolve()
    if not issue_folder_path.is_dir():
        continue

    issue_script = issue_folder_path.joinpath(DEFAULT_SCRIPT_NAME).resolve()
    if not issue_script.is_file():
        continue

    issues.append(issue_folder)

title_to_issue_folder = {}

issue_titles = []
default_index = 0
for i, issue in enumerate(issues):
    if not issue:
        continue
    if "gh-template" in issue:
        # Ignore template
        continue
    title_to_issue_folder[issue] = issue
    issue_titles.append(issue)

# Add empty state:
issue_titles.sort(reverse=True)
issue_titles = [""] + issue_titles
query_params = initial_query_params()
if "issue" in query_params and query_params["issue"]:
    query_param_issue = str(query_params["issue"][0])
    if query_param_issue in issue_titles:
        default_index = issue_titles.index(query_param_issue)

selected_issue = st.selectbox("Select Issue", options=issue_titles, index=default_index)

st.experimental_set_query_params(issue=selected_issue)


@st.cache_data(ttl=60 * 5)  # cache for 5 minutes
def request_github_issue(issue_number: str) -> Union[str, None]:
    try:
        with urllib.request.urlopen(
            f"https://api.github.com/repos/streamlit/streamlit/issues/{issue_number}"
        ) as response:
            return response.read()
    except Exception as ex:
        print(ex, flush=True)
    return None


if selected_issue:
    selected_issue_folder = title_to_issue_folder[selected_issue]
    selected_issue_folder_path = path_to_issues.joinpath(
        selected_issue_folder
    ).resolve()

    with st.container():
        if (
            selected_issue_folder.startswith("gh-")
            and selected_issue_folder.replace("gh-", "").isnumeric()
        ):
            issue_number = selected_issue_folder.replace("gh-", "")
            # Request issue from GitHub API and extract the body:
            try:
                response = request_github_issue(issue_number)
                if response:
                    data = json.loads(response)
                    if "title" in data:
                        issue_title = data["title"].strip()
                        st.markdown(f"**{issue_title}**")
                    BADGES = f"""
<a href="https://github.com/streamlit/streamlit/issues/{issue_number}" title="Issue State" target="_blank"><img src="https://img.shields.io/github/issues/detail/state/streamlit/streamlit/{issue_number}?style=flat-square"></a>
<a href="https://github.com/streamlit/streamlit/issues/{issue_number}" title="Issue Last Update" target="_blank"><img src="https://img.shields.io/github/issues/detail/last-update/streamlit/streamlit/{issue_number}?style=flat-square"></a>
<a href="https://github.com/streamlit/streamlit/issues/{issue_number}" title="Issue Created at" target="_blank"><img src="https://img.shields.io/github/issues/detail/age/streamlit/streamlit/{issue_number}?style=flat-square"></a>
<a href="https://github.com/streamlit/streamlit/issues/{issue_number}" title="Issue Comments" target="_blank"><img src="https://img.shields.io/github/issues/detail/comments/streamlit/streamlit/{issue_number}?style=flat-square"></a>
<a href="https://github.com/streamlit/streamlit/issues/{issue_number}" title="Issue Labels" target="_blank"><img src="https://img.shields.io/github/issues/detail/label/streamlit/streamlit/{issue_number}?style=flat-square&label=%20"></a>
"""
                    st.markdown(BADGES, unsafe_allow_html=True)
                    issue_body = data["body"]
                    if issue_body:
                        with st.expander("Issue Description"):
                            st.markdown(issue_body, unsafe_allow_html=True)
                            st.markdown("---")
                            st.caption(
                                "Add the following markdown badge to the issue on Github to provide a link to this app:"
                            )
                            st.code(
                                f"[![Open in Streamlit Cloud](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://issues.streamlitapp.com/?issue={selected_issue})",
                                language="markdown",
                            )
                        
                        steps_to_reproduce = None
                        
                        # New issue template
                        if "### Steps To Reproduce" in issue_body:
                            steps_to_reproduce = issue_body.split("### Steps To Reproduce")[
                                1
                            ].split("### Is this a regression")[0].replace("###", "#####")
                        
                        # Old issue template
                        elif "### Steps to reproduce" in issue_body:
                            # Extract from issue body
                            steps_to_reproduce = issue_body.split("### Steps to reproduce")[
                                1
                            ].split("###")[0]
                            # Remove markdown code blocks via regex
                            steps_to_reproduce = re.sub(
                                r"```.*?```",
                                "```\nSee the code below...\n```",
                                steps_to_reproduce,
                                flags=re.DOTALL,
                            )
                            # Remove Streamlit badge
                            steps_to_reproduce = re.sub(
                                r"\[!\[Open in Streamlit Cloud\]\(https://static.streamlit.io/badges/streamlit_badge_black_white.svg\)\]\(https:.*?\)",
                                "",
                                steps_to_reproduce,
                            )
    
                        if steps_to_reproduce:
                            with st.expander("Steps to reproduce"):
                                st.markdown(steps_to_reproduce, unsafe_allow_html=True)
            except Exception as ex:
                print(ex, flush=True)
    
        with st.expander("Source Code", expanded=True):
            with open(
                selected_issue_folder_path.joinpath(DEFAULT_SCRIPT_NAME).resolve(),
                encoding="UTF-8",
            ) as f:
                st.code(f.read(), language="python")

    if (
        selected_issue_folder_path.joinpath("requirements.txt").exists()
        or selected_issue_folder_path.joinpath("Pipfile").exists()
    ):
        st.info(
            f"""
This issue script requires additional dependencies to run.
Therefore, it needs to be [deployed separately](https://share.streamlit.io/streamlit/st-issues/main/{DEFAULT_ISSUES_FOLDER}/{selected_issue_folder}/{DEFAULT_SCRIPT_NAME}).
In case the app embedded below is not running, you can deploy it yourself [here](https://share.streamlit.io/deploy?repository=streamlit/st-issues&branch=main&mainModule={DEFAULT_ISSUES_FOLDER}/{selected_issue_folder}/{DEFAULT_SCRIPT_NAME}).
""",
        )
        st.caption(
            f"[Open in a new tab](https://share.streamlit.io/streamlit/st-issues/main/{DEFAULT_ISSUES_FOLDER}/{selected_issue_folder}/{DEFAULT_SCRIPT_NAME})"
        )
        # embed streamlit docs in a streamlit app
        components.iframe(
            f"https://share.streamlit.io/streamlit/st-issues/main/{DEFAULT_ISSUES_FOLDER}/{selected_issue_folder}/{DEFAULT_SCRIPT_NAME}?embed=true",
            height=650,
        )
    else:
        # Run the issue script
        exec(open(selected_issue_folder_path.joinpath(DEFAULT_SCRIPT_NAME)).read())
