import pathlib
import platform
import re
from typing import TypedDict

import streamlit as st
import streamlit.components.v1 as components

from app.utils.agent_wiki import WikiIssueRepro, fetch_wiki_document_text, fetch_wiki_issue_repros
from app.utils.github_utils import get_issue_data

st.set_page_config(page_title="Issue explorer", page_icon="🚧")
st.title("🚧 Issue explorer")

st.caption(
    f"""
A collection of Streamlit apps to replicate issues and bugs. Add your issue script [here](https://github.com/streamlit/st-issues).
Reproductions published in the [agent wiki](https://github.com/streamlit/streamlit/wiki) are included as well.

Running with Python {platform.python_version()} and Streamlit {st.__version__}.
"""
)
DEFAULT_SELECTION = ""
DEFAULT_SCRIPT_NAME = "app.py"
DEFAULT_ISSUES_FOLDER = "issues"

LOCAL_SOURCE = "local"
WIKI_SOURCE = "wiki"


class IssueCase(TypedDict):
    name: str
    source: str
    issue_number: int | None
    local_path: pathlib.Path | None
    wiki_repro: WikiIssueRepro | None


def initial_query_params() -> dict:
    """Sync url params to session state on first load.

    When page is first loaded, or if current params are empty, sync url params to
    session state. Afterwards, just return local copy.
    """
    if "initial_query_params_issue" not in st.session_state or not st.session_state["initial_query_params_issue"]:
        st.session_state["initial_query_params_issue"] = st.query_params.to_dict()
    return st.session_state["initial_query_params_issue"]


def issue_folder_to_number(folder_name: str) -> int | None:
    match = re.fullmatch(r"gh-(\d+)", folder_name)
    return int(match.group(1)) if match else None


path_of_script = pathlib.Path(__file__).parent.resolve()
path_to_issues = pathlib.Path(path_of_script).parent.joinpath(DEFAULT_ISSUES_FOLDER).resolve()

cases: dict[str, IssueCase] = {}

# Local reproduction cases merged into st-issues. These take priority over the
# agent wiki since they have been reviewed and adapted for this app.
for issue_folder in (p.name for p in path_to_issues.iterdir()):
    if not issue_folder or "gh-template" in issue_folder:
        # Ignore the template folder.
        continue

    issue_folder_path = path_to_issues.joinpath(issue_folder).resolve()
    if not issue_folder_path.is_dir():
        continue

    issue_script = issue_folder_path.joinpath(DEFAULT_SCRIPT_NAME).resolve()
    if not issue_script.is_file():
        continue

    cases[issue_folder] = {
        "name": issue_folder,
        "source": LOCAL_SOURCE,
        "issue_number": issue_folder_to_number(issue_folder),
        "local_path": issue_folder_path,
        "wiki_repro": None,
    }

# Reproduction cases published in the agent wiki. Only added if no local case
# already exists for the same issue number (local cases win).
wiki_repros, wiki_error = fetch_wiki_issue_repros()
if wiki_error:
    print("Failed to load agent wiki reproductions:", wiki_error, flush=True)

for wiki_issue_number, wiki_repro in wiki_repros.items():
    case_name = f"gh-{wiki_issue_number}"
    if case_name in cases:
        continue
    cases[case_name] = {
        "name": case_name,
        "source": WIKI_SOURCE,
        "issue_number": wiki_issue_number,
        "local_path": None,
        "wiki_repro": wiki_repro,
    }


def issue_sort_key(case_name: str) -> tuple[int, int, str]:
    match = re.fullmatch(r"gh-(\d+)", case_name)
    if match:
        return (1, int(match.group(1)), case_name)
    return (0, 0, case_name)


def format_case(case_name: str) -> str:
    case = cases.get(case_name)
    if case and case["source"] == WIKI_SOURCE:
        return f"{case_name} (agent wiki)"
    return case_name


# Add empty state:
case_names = sorted(cases.keys(), key=issue_sort_key, reverse=True)
case_names = ["", *case_names]

default_index = 0
query_params = initial_query_params()
if query_params.get("issue"):
    query_param_issue = str(query_params["issue"])
    if query_param_issue in case_names:
        default_index = case_names.index(query_param_issue)

selected_issue = st.selectbox(
    "Select Issue",
    options=case_names,
    index=default_index,
    format_func=format_case,
)

print("Selected issue:", selected_issue, flush=True)

st.query_params["issue"] = selected_issue


def get_case_source_code(case: IssueCase) -> tuple[str | None, str | None]:
    """Return the reproduction script content for a case and an optional error."""
    if case["source"] == LOCAL_SOURCE and case["local_path"] is not None:
        script_path = case["local_path"].joinpath(DEFAULT_SCRIPT_NAME)
        return script_path.read_text(encoding="utf-8"), None

    wiki_repro = case["wiki_repro"]
    if wiki_repro is None:
        return None, "No reproduction script is available for this case."
    return fetch_wiki_document_text(wiki_repro["repro_app_path"])


if selected_issue:
    case = cases[selected_issue]
    issue_number = case["issue_number"]
    source_code, source_error = get_case_source_code(case)

    with st.container():
        if issue_number is not None:
            # Request issue from GitHub API and extract the body:
            try:
                data = get_issue_data("streamlit/streamlit", str(issue_number))
                if data:
                    if "title" in data:
                        issue_title = data["title"].strip()
                        st.markdown(f"**{issue_title}**")
                    badges = [
                        f"[![Issue State](https://img.shields.io/github/issues/detail/state/streamlit/streamlit/{issue_number}?style=flat-square)](https://github.com/streamlit/streamlit/issues/{issue_number})",
                        f"[![Issue Last Update](https://img.shields.io/github/issues/detail/last-update/streamlit/streamlit/{issue_number}?style=flat-square)](https://github.com/streamlit/streamlit/issues/{issue_number})",
                        f"[![Issue Created at](https://img.shields.io/github/issues/detail/age/streamlit/streamlit/{issue_number}?style=flat-square)](https://github.com/streamlit/streamlit/issues/{issue_number})",
                        f"[![Issue Comments](https://img.shields.io/github/issues/detail/comments/streamlit/streamlit/{issue_number}?style=flat-square)](https://github.com/streamlit/streamlit/issues/{issue_number})",
                        f"[![Issue Labels](https://img.shields.io/github/issues/detail/label/streamlit/streamlit/{issue_number}?style=flat-square&label=%20)](https://github.com/streamlit/streamlit/issues/{issue_number})",
                    ]
                    st.markdown(" ".join(badges))
                    issue_body = data["body"]
                    if issue_body:
                        with st.expander("Issue Description"):
                            st.markdown(issue_body)
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
                            steps_to_reproduce = (
                                issue_body.split("### Steps To Reproduce")[1]
                                .split("### Is this a regression")[0]
                                .replace("###", "#####")
                            )

                        # Old issue template
                        elif "### Steps to reproduce" in issue_body:
                            # Extract from issue body
                            steps_to_reproduce = issue_body.split("### Steps to reproduce")[1].split("###")[0]
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
                                st.markdown(steps_to_reproduce)
            except Exception as ex:
                print(ex, flush=True)

        if case["source"] == WIKI_SOURCE and case["wiki_repro"] is not None:
            wiki_repro = case["wiki_repro"]
            verify_suffix = ""
            if wiki_repro["verify_path"]:
                verify_suffix = " A companion `repro_app_verify.py` is available in the same folder."
            st.info(
                f"This reproduction is loaded from the "
                f"[agent wiki]({wiki_repro['folder_url']}) and has not been reviewed. "
                f"[View `repro_app.py`]({wiki_repro['repro_app_source_url']}).{verify_suffix}",
                icon=":material/menu_book:",
            )

        with st.expander("Source Code", expanded=True):
            if source_error or source_code is None:
                st.error(source_error or "The reproduction script could not be loaded.")
            else:
                st.code(source_code, language="python")

    if case["source"] == LOCAL_SOURCE and case["local_path"] is not None:
        selected_issue_folder_path = case["local_path"]
        if (
            selected_issue_folder_path.joinpath("requirements.txt").exists()
            or selected_issue_folder_path.joinpath("Pipfile").exists()
        ):
            st.info(
                f"""
This issue script requires additional dependencies to run.
Therefore, it needs to be [deployed separately](https://share.streamlit.io/streamlit/st-issues/main/{DEFAULT_ISSUES_FOLDER}/{selected_issue}/{DEFAULT_SCRIPT_NAME}).
In case the app embedded below is not running, you can deploy it yourself [here](https://share.streamlit.io/deploy?repository=streamlit/st-issues&branch=main&mainModule={DEFAULT_ISSUES_FOLDER}/{selected_issue}/{DEFAULT_SCRIPT_NAME}).
""",
            )
            st.caption(
                f"[Open in a new tab](https://share.streamlit.io/streamlit/st-issues/main/{DEFAULT_ISSUES_FOLDER}/{selected_issue}/{DEFAULT_SCRIPT_NAME})"
            )
            # embed streamlit docs in a streamlit app
            components.iframe(
                f"https://share.streamlit.io/streamlit/st-issues/main/{DEFAULT_ISSUES_FOLDER}/{selected_issue}/{DEFAULT_SCRIPT_NAME}?embed=true",
                height=650,
            )
        elif source_code is not None:
            # Run the issue script
            exec(source_code)  # ruff:ignore[exec-builtin]
    elif source_code is not None:
        # Run the reproduction app loaded from the agent wiki.
        exec(source_code)  # ruff:ignore[exec-builtin]
