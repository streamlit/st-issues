import json
import os
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict, List, Optional
from zipfile import ZipFile

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests  # type: ignore
import streamlit as st
import streamlit.components.v1 as components

from pages.utils.smokeshow import extract_and_upload_coverage_report

# Set page configuration
st.set_page_config(page_title="Code Coverage (Frontend)", page_icon="☂️", layout="wide")

# GitHub API configuration
GITHUB_API_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token {st.secrets['github']['token']}",
}


@st.cache_data(show_spinner=False)
def deploy_coverage_report(run_id: int) -> Optional[str]:
    """Deploy the HTML coverage report to smokeshow."""
    # Fetch artifacts
    artifacts = fetch_artifacts(run_id)

    html_report_artifact = None
    for artifact in artifacts:
        if artifact["name"] == "vitest_coverage_html":
            html_report_artifact = artifact
            break

    if not html_report_artifact:
        st.error("No HTML coverage report found for this run.")
        return None

    artifact_content = download_artifact(html_report_artifact["archive_download_url"])

    if not artifact_content:
        st.error("Failed to download the HTML coverage report.")
        return None

    # Extract and upload to smokeshow
    return extract_and_upload_coverage_report(artifact_content)


# Function to download, extract, upload and display the HTML coverage report
@st.dialog("Coverage Report", width="large")
def display_coverage_report_dialog(run_id: int):
    """Download, extract, upload and display the HTML coverage report in an iframe."""
    # Download the artifact
    with st.spinner("Downloading and deploying the coverage report..."):
        report_url = deploy_coverage_report(run_id)
        if not report_url:
            st.error("Failed to deploy the HTML coverage report.")
            return
        st.caption(f"[Open fullscreen :material/open_in_new:]({report_url})")
        # Display the iframe in a dialog
        components.iframe(report_url, height=600, scrolling=True)


# Get PR number from query parameters if available
query_params = st.query_params
pr_number = query_params.get("pr")

# Page title and description
st.title("☂️ Test Coverage (Frontend)")
if pr_number is not None:
    st.caption(f"""
    Analyzing coverage for [PR #{pr_number}](https://github.com/streamlit/streamlit/pull/{pr_number})
    """)
    # Default values for PR mode
    since_date = None
    workflow_runs_limit = 1
    uploaded_file = None
else:
    st.caption("""
    This app shows frontend test coverage trends over time and allows you to analyze detailed coverage data for specific commits.
    """)

    time_period = st.sidebar.selectbox(
        "Time period",
        options=["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
        help="The time period to display coverage data for. But it will still only load the last X workflow runs as defined by the slider below.",
        index=3,
    )
    workflow_runs_limit = st.sidebar.slider(
        "Number of workflow runs",
        min_value=50,
        max_value=250,
        value=50,
        step=50,
        help="This is equivalent to the number of commits to develop to include in the analysis.",
    )

    # Add file uploader for manual coverage JSON file to the sidebar
    st.sidebar.divider()
    uploaded_file = st.sidebar.file_uploader(
        "Manual upload of Vitest coverage JSON file",
        type=["json"],
        accept_multiple_files=False,
    )

    # Convert time period to date
    if time_period == "Last 7 days":
        since_date = datetime.now() - timedelta(days=7)
    elif time_period == "Last 30 days":
        since_date = datetime.now() - timedelta(days=30)
    elif time_period == "Last 90 days":
        since_date = datetime.now() - timedelta(days=90)
    else:
        since_date = None


def parse_vitest_coverage_json(coverage_file):
    """Parse a Vitest JSON summary report file and return the data"""
    try:
        # Parse the JSON data
        coverage_data = json.load(coverage_file)

        # Create a dictionary to store coverage information
        coverage_info = {}

        # Define prefix to remove
        prefix_to_remove = "/home/runner/work/streamlit/streamlit/frontend/"

        # Process each file in the coverage data (excluding the "total" key)
        for file_path, file_data in coverage_data.items():
            if file_path == "total":
                continue

            # Remove the prefix from the file path if it exists
            clean_path = file_path
            if file_path.startswith(prefix_to_remove):
                clean_path = file_path[len(prefix_to_remove) :]

            # Extract the file name from the path
            file_name = os.path.basename(clean_path)

            # Extract relevant metrics
            lines_total = file_data["lines"]["total"]
            lines_covered = file_data["lines"]["covered"]
            functions_total = file_data["functions"]["total"]
            functions_covered = file_data["functions"]["covered"]
            branches_total = file_data["branches"]["total"]
            branches_covered = file_data["branches"]["covered"]

            # Calculate coverage percentages
            lines_pct = file_data["lines"]["pct"]
            functions_pct = file_data["functions"]["pct"]
            branches_pct = file_data["branches"]["pct"]

            # Store information
            coverage_info[clean_path] = {
                "file_name": file_name,
                "file_path": clean_path,
                "lines_total": lines_total,
                "lines_covered": lines_covered,
                "lines_pct": lines_pct,
                "functions_total": functions_total,
                "functions_covered": functions_covered,
                "functions_pct": functions_pct,
                "branches_total": branches_total,
                "branches_covered": branches_covered,
                "branches_pct": branches_pct,
            }

        return coverage_info, coverage_data.get("total", {})

    except json.JSONDecodeError:
        st.error(
            "Invalid JSON file. Please ensure you're uploading a valid Vitest JSON summary report."
        )
        return None, None
    except Exception as e:
        st.error(f"Error processing coverage data: {str(e)}")
        return None, None


@st.cache_data(
    ttl=60 * 60 * 12, show_spinner="Fetching workflow runs..."
)  # cache for 12 hours
def fetch_workflow_runs(
    workflow_name: str, limit: int = 50, since: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """Fetch workflow runs for a specific workflow."""
    all_runs: List[Dict[str, Any]] = []
    page = 1
    per_page = 100  # GitHub API maximum per page

    # Convert since to ISO format if provided
    since_param = f"&created=>{since.strftime('%Y-%m-%dT%H:%M:%SZ')}" if since else ""

    while len(all_runs) < limit:
        try:
            response = requests.get(
                f"https://api.github.com/repos/streamlit/streamlit/actions/workflows/{workflow_name}/runs?branch=develop&status=success&per_page={per_page}&page={page}{since_param}",
                headers=GITHUB_API_HEADERS,
                timeout=30,
            )

            if response.status_code != 200:
                st.error(f"Error fetching workflow runs: {response.status_code}")
                break

            data = response.json()
            runs = data.get("workflow_runs", [])

            if not runs:
                break  # No more runs to fetch

            all_runs.extend(runs)

            if len(runs) < per_page:
                break  # No more pages to fetch

            page += 1

        except Exception as e:
            st.error(f"Error fetching workflow runs: {e}")
            break

    return all_runs[:limit]


@st.cache_data(show_spinner="Fetching artifacts...")
def fetch_artifacts(run_id: int) -> List[Dict[str, Any]]:
    """Fetch artifacts for a specific workflow run."""
    try:
        response = requests.get(
            f"https://api.github.com/repos/streamlit/streamlit/actions/runs/{run_id}/artifacts",
            headers=GITHUB_API_HEADERS,
            timeout=30,
        )

        if response.status_code != 200:
            print(f"Error fetching artifacts: {response.status_code}", response.text)
            return []

        return response.json().get("artifacts", [])
    except Exception as e:
        print(f"Error fetching artifacts: {e}")
        return []


@st.cache_data(show_spinner=False)
def download_artifact(artifact_url: str) -> Optional[bytes]:
    """Download an artifact from GitHub Actions."""
    try:
        response = requests.get(
            artifact_url,
            headers=GITHUB_API_HEADERS,
            timeout=60,
        )

        if response.status_code != 200:
            st.error(f"Error downloading artifact: {response.status_code}")
            return None

        return response.content
    except Exception as e:
        st.error(f"Error downloading artifact: {e}")
        return None


@st.cache_data(show_spinner=False)
def get_coverage_data_from_artifact(run_id: int) -> Optional[Dict[str, Any]]:
    """Get coverage data from the artifact of a workflow run."""
    artifacts = fetch_artifacts(run_id)

    coverage_json_artifact = None
    for artifact in artifacts:
        if artifact["name"] == "vitest_coverage_json":
            coverage_json_artifact = artifact
            break

    if not coverage_json_artifact:
        return None

    # Download the artifact
    artifact_content = download_artifact(coverage_json_artifact["archive_download_url"])

    if not artifact_content:
        return None

    # Extract the coverage JSON file from the zip
    try:
        with ZipFile(BytesIO(artifact_content)) as zip_file:
            file_list = zip_file.namelist()
            # Find a JSON file that contains coverage data
            json_file = next((f for f in file_list if f.endswith(".json")), None)

            if json_file:
                with zip_file.open(json_file) as coverage_file:
                    _, total_data = parse_vitest_coverage_json(coverage_file)
                    if total_data:
                        # Return key metrics from the total data
                        return {
                            "lines_total": total_data["lines"]["total"],
                            "lines_covered": total_data["lines"]["covered"],
                            "lines_pct": total_data["lines"]["pct"],
                            "functions_total": total_data["functions"]["total"],
                            "functions_covered": total_data["functions"]["covered"],
                            "functions_pct": total_data["functions"]["pct"],
                            "branches_total": total_data["branches"]["total"],
                            "branches_covered": total_data["branches"]["covered"],
                            "branches_pct": total_data["branches"]["pct"],
                        }
    except Exception as e:
        st.error(f"Error extracting coverage data: {e}")

    return None


@st.cache_data(show_spinner=False)
def get_html_report_url(run_id: int) -> Optional[str]:
    """Get the download URL for the HTML coverage report artifact."""
    artifacts = fetch_artifacts(run_id)

    html_report_artifact = None
    for artifact in artifacts:
        if artifact["name"] == "vitest_coverage_html":
            html_report_artifact = artifact
            break

    if html_report_artifact:
        # Transform API URL to non-API GitHub URL format
        artifact_id = html_report_artifact["id"]
        return f"https://github.com/streamlit/streamlit/actions/runs/{run_id}/artifacts/{artifact_id}"

    return None


def display_coverage_details(
    coverage_data, total_data, html_report_url=None, run_id=None
):
    """Display detailed coverage information."""
    # Convert coverage data to DataFrame for easier manipulation
    coverage_df = pd.DataFrame(
        [
            {
                "Filename": info["file_name"],
                "Path": info["file_path"],
                "Lines Total": info["lines_total"],
                "Lines Covered": info["lines_covered"],
                "Lines Coverage %": info["lines_pct"],
                "Functions Total": info["functions_total"],
                "Functions Covered": info["functions_covered"],
                "Functions Coverage %": info["functions_pct"],
                "Branches Total": info["branches_total"],
                "Branches Covered": info["branches_covered"],
                "Branches Coverage %": info["branches_pct"],
            }
            for _, info in coverage_data.items()
        ]
    )

    # Check if we have any data
    if len(coverage_df) == 0:
        st.warning("No coverage data found in the uploaded file.")
        return

    # Display overall metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Files", len(coverage_df))
        st.metric("Total Lines", total_data["lines"]["total"])
    with col2:
        st.metric("Lines Coverage", f"{total_data['lines']['pct']:.2f}%")
        st.metric("Functions Coverage", f"{total_data['functions']['pct']:.2f}%")
    with col3:
        st.metric("Branches Coverage", f"{total_data['branches']['pct']:.2f}%")
        st.metric("Statements Coverage", f"{total_data['statements']['pct']:.2f}%")

    # Create gauge charts for overall coverage metrics
    col1, col2 = st.columns(2)

    with col1:
        # Lines coverage gauge
        fig_lines = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=total_data["lines"]["pct"],
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "Lines Coverage"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, 60], "color": "red"},
                        {"range": [60, 80], "color": "orange"},
                        {"range": [80, 100], "color": "green"},
                    ],
                    "threshold": {
                        "line": {"color": "black", "width": 4},
                        "thickness": 0.75,
                        "value": total_data["lines"]["pct"],
                    },
                },
            )
        )
        st.plotly_chart(fig_lines, use_container_width=True)

    with col2:
        # Branches coverage gauge
        fig_branches = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=total_data["branches"]["pct"],
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "Branches Coverage"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, 60], "color": "red"},
                        {"range": [60, 80], "color": "orange"},
                        {"range": [80, 100], "color": "green"},
                    ],
                    "threshold": {
                        "line": {"color": "black", "width": 4},
                        "thickness": 0.75,
                        "value": total_data["branches"]["pct"],
                    },
                },
            )
        )
        st.plotly_chart(fig_branches, use_container_width=True)

    # Display file-level coverage
    st.header("File Coverage Details")

    # Sort by coverage percentage (ascending)
    coverage_df = coverage_df.sort_values("Lines Coverage %", ascending=False)

    # Create GitHub links for the Path column
    coverage_df["File"] = coverage_df["Path"].apply(
        lambda x: f"https://github.com/streamlit/streamlit/tree/develop/frontend/{x}"
    )

    # Display the dataframe with coverage information and GitHub links
    st.dataframe(
        coverage_df,
        column_config={
            "Lines Coverage %": st.column_config.ProgressColumn(
                "Lines Coverage %",
                help="Percentage of lines covered by tests",
                format="%d%%",
                min_value=0,
                max_value=100,
            ),
            "Functions Coverage %": st.column_config.ProgressColumn(
                "Functions Coverage %",
                help="Percentage of functions covered by tests",
                format="%d%%",
                min_value=0,
                max_value=100,
            ),
            "Branches Coverage %": st.column_config.ProgressColumn(
                "Branches Coverage %",
                help="Percentage of branches covered by tests",
                format="%d%%",
                min_value=0,
                max_value=100,
            ),
            "File": st.column_config.LinkColumn(
                "File",
                help="View file in GitHub repository",
                display_text="https://github.com/streamlit/streamlit/tree/develop/frontend/(.*)",
                pinned=True,
            ),
        },
        hide_index=True,
        column_order=[
            "File",
            "Lines Covered",
            "Lines Total",
            "Lines Coverage %",
            "Functions Covered",
            "Functions Total",
            "Functions Coverage %",
            "Branches Covered",
            "Branches Total",
            "Branches Coverage %",
        ],
    )

    col1, col2 = st.columns(2)
    # Add HTML report download button if URL is available
    if html_report_url:
        col1.link_button(
            label=":material/download: Download HTML Coverage Report",
            url=html_report_url,
            use_container_width=True,
        )
    if run_id:
        if col2.button(":material/preview: View PR Report", use_container_width=True):
            display_coverage_report_dialog(run_id=run_id)

    # Create visualizations for file coverage
    if len(coverage_df) > 0:
        # Create a treemap visualization
        st.subheader("Coverage Treemap")

        # Extract package (top-level directory) and directory structure
        coverage_df["Package"] = coverage_df["Path"].apply(
            lambda x: x.split("/")[0] if "/" in x else "root"
        )

        # Extract directory structure (last directory component)
        coverage_df["Directory"] = coverage_df["Path"].apply(
            lambda x: os.path.dirname(x).replace("\\", "/").split("/")[-1]
            if os.path.dirname(x)
            else "root"
        )

        fig = px.treemap(
            coverage_df,
            path=["Package", "Directory", "Filename"],
            values="Lines Total",
            color="Lines Coverage %",
            color_continuous_scale=["red", "orange", "green"],
            range_color=[0, 100],
            hover_data=[
                "Lines Covered",
                "Lines Total",
                "Functions Coverage %",
                "Branches Coverage %",
            ],
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Coverage by File")

        # Limit to top 20 files if there are many
        display_df = coverage_df.sort_values("Lines Coverage %", ascending=True)
        if len(coverage_df) > 20:
            display_df = display_df.head(20)
            st.info(
                "Showing only the 20 files with the lowest coverage. Use the table above to see all files."
            )

        fig = px.bar(
            display_df,
            y="Filename",
            x="Lines Coverage %",
            orientation="h",
            color="Lines Coverage %",
            color_continuous_scale=["red", "orange", "green"],
            range_color=[0, 100],
            labels={
                "Lines Coverage %": "Coverage Percentage",
                "Filename": "Filename",
            },
        )

        fig.update_layout(yaxis={"categoryorder": "total descending"})
        st.plotly_chart(fig, use_container_width=True)

        # Display coverage distribution
        st.subheader("Coverage Distribution of Files")

        # Create coverage bins
        bins = [0, 20, 40, 60, 80, 100]
        labels = ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"]

        coverage_df["Coverage Range"] = pd.cut(
            coverage_df["Lines Coverage %"],
            bins=bins,
            labels=labels,
            include_lowest=True,
        )

        # Count files in each bin
        distribution = coverage_df["Coverage Range"].value_counts().reindex(labels)

        # Create a pie chart
        fig = px.pie(
            names=distribution.index,
            values=distribution.values,
            color=distribution.index,
            color_discrete_map={
                "0-20%": "red",
                "20-40%": "orangered",
                "40-60%": "orange",
                "60-80%": "yellowgreen",
                "80-100%": "green",
            },
        )

        st.plotly_chart(fig, use_container_width=True)


def fetch_pr_info(pr_number: str) -> Optional[Dict[str, Any]]:
    """Fetch information about a PR from GitHub API."""
    try:
        response = requests.get(
            f"https://api.github.com/repos/streamlit/streamlit/pulls/{pr_number}",
            headers=GITHUB_API_HEADERS,
            timeout=30,
        )

        if response.status_code != 200:
            st.error(f"Error fetching PR info: {response.status_code}")
            return None

        return response.json()
    except Exception as e:
        st.error(f"Error fetching PR info: {e}")
        return None


def fetch_workflow_runs_for_commit(commit_sha: str) -> List[Dict[str, Any]]:
    """Fetch workflow runs for a specific commit."""
    try:
        response = requests.get(
            f"https://api.github.com/repos/streamlit/streamlit/actions/workflows/js-tests.yml/runs?head_sha={commit_sha}&status=success",
            headers=GITHUB_API_HEADERS,
            timeout=30,
        )

        if response.status_code != 200:
            st.error(f"Error fetching workflow runs for commit: {response.status_code}")
            return []

        return response.json().get("workflow_runs", [])
    except Exception as e:
        st.error(f"Error fetching workflow runs for commit: {e}")
        return []


def get_latest_develop_coverage() -> Optional[Dict[str, Any]]:
    """Get coverage data for the latest successful workflow run on develop."""
    # Fetch the latest successful workflow run on develop
    latest_runs = fetch_workflow_runs("js-tests.yml", limit=1)
    if not latest_runs:
        st.error("No recent workflow runs found on develop branch.")
        return None

    latest_run = latest_runs[0]
    # Get coverage data for this run
    coverage_data = get_coverage_data_from_artifact(latest_run["id"])
    if not coverage_data:
        st.error("Could not fetch coverage data for the latest develop commit.")
        return None

    return {
        "run_id": latest_run["id"],
        "commit_sha": latest_run["head_sha"][:7],
        "commit_url": f"https://github.com/streamlit/streamlit/commit/{latest_run['head_sha']}",
        "created_at": datetime.strptime(latest_run["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
        "lines_pct": coverage_data["lines_pct"],
        "functions_pct": coverage_data["functions_pct"],
        "branches_pct": coverage_data["branches_pct"],
        "lines_total": coverage_data["lines_total"],
        "lines_covered": coverage_data["lines_covered"],
        "functions_total": coverage_data["functions_total"],
        "functions_covered": coverage_data["functions_covered"],
        "branches_total": coverage_data["branches_total"],
        "branches_covered": coverage_data["branches_covered"],
        "run_url": latest_run["html_url"],
    }


def get_pr_coverage(pr_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get coverage data for a PR's head commit."""
    head_sha = pr_info["head"]["sha"]
    # Fetch workflow runs for this commit
    pr_runs = fetch_workflow_runs_for_commit(head_sha)

    if not pr_runs:
        st.error(f"No successful workflow runs found for PR commit {head_sha[:7]}.")
        return None

    # Get the latest successful run
    pr_run = pr_runs[0]
    # Get coverage data for this run
    coverage_data = get_coverage_data_from_artifact(pr_run["id"])
    if not coverage_data:
        st.error(f"Could not fetch coverage data for PR commit {head_sha[:7]}.")
        return None

    return {
        "run_id": pr_run["id"],
        "commit_sha": head_sha[:7],
        "commit_url": f"https://github.com/streamlit/streamlit/commit/{head_sha}",
        "created_at": datetime.strptime(pr_run["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
        "lines_pct": coverage_data["lines_pct"],
        "functions_pct": coverage_data["functions_pct"],
        "branches_pct": coverage_data["branches_pct"],
        "lines_total": coverage_data["lines_total"],
        "lines_covered": coverage_data["lines_covered"],
        "functions_total": coverage_data["functions_total"],
        "functions_covered": coverage_data["functions_covered"],
        "branches_total": coverage_data["branches_total"],
        "branches_covered": coverage_data["branches_covered"],
        "run_url": pr_run["html_url"],
    }


def display_pr_coverage_comparison(
    pr_coverage: Dict[str, Any], develop_coverage: Dict[str, Any]
):
    """Display a comparison of PR coverage against develop branch coverage."""
    st.subheader("PR Coverage Comparison")

    # Calculate coverage changes
    lines_coverage_change = pr_coverage["lines_pct"] - develop_coverage["lines_pct"]
    functions_coverage_change = (
        pr_coverage["functions_pct"] - develop_coverage["functions_pct"]
    )
    branches_coverage_change = (
        pr_coverage["branches_pct"] - develop_coverage["branches_pct"]
    )

    # Determine if changes are positive or negative
    lines_delta = "+" if lines_coverage_change >= 0 else ""
    functions_delta = "+" if functions_coverage_change >= 0 else ""
    branches_delta = "+" if branches_coverage_change >= 0 else ""

    # Create comparison columns
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Lines Coverage",
            f"{pr_coverage['lines_pct']:.2f}%",
            f"{lines_delta}{lines_coverage_change:.2f}%",
            delta_color="normal" if lines_coverage_change >= 0 else "inverse",
        )

    with col2:
        st.metric(
            "Functions Coverage",
            f"{pr_coverage['functions_pct']:.2f}%",
            f"{functions_delta}{functions_coverage_change:.2f}%",
            delta_color="normal" if functions_coverage_change >= 0 else "inverse",
        )

    with col3:
        st.metric(
            "Branches Coverage",
            f"{pr_coverage['branches_pct']:.2f}%",
            f"{branches_delta}{branches_coverage_change:.2f}%",
            delta_color="normal" if branches_coverage_change >= 0 else "inverse",
        )

    # Display additional PR information
    st.markdown(f"""
    **PR Commit:** [{pr_coverage["commit_sha"]}]({pr_coverage["commit_url"]}) |
    **Develop Commit:** [{develop_coverage["commit_sha"]}]({develop_coverage["commit_url"]})

    **PR Workflow Run:** [View Run]({pr_coverage["run_url"]}) |
    **Develop Workflow Run:** [View Run]({develop_coverage["run_url"]})
    """)

    # Get HTML report URLs
    pr_html_report_url = get_html_report_url(pr_coverage["run_id"])
    develop_html_report_url = get_html_report_url(develop_coverage["run_id"])

    # Add HTML report download buttons if URLs are available
    col1, col2 = st.columns(2)
    with col1:
        if pr_html_report_url:
            st.link_button(
                label=":material/download: Download PR Report",
                url=pr_html_report_url,
                use_container_width=True,
            )
            if st.button(":material/preview: View PR Report", use_container_width=True):
                display_coverage_report_dialog(pr_coverage["run_id"])

    with col2:
        if develop_html_report_url:
            st.link_button(
                label=":material/download: Download Develop Report",
                url=develop_html_report_url,
                use_container_width=True,
            )
            if st.button(
                ":material/preview: View Develop Report", use_container_width=True
            ):
                display_coverage_report_dialog(develop_coverage["run_id"])


# PR mode processing
if pr_number is not None:
    # Fetch PR info
    pr_info = fetch_pr_info(pr_number)
    if not pr_info:
        st.error(f"Could not fetch information for PR #{pr_number}")
        st.stop()

    # Get coverage for PR and develop
    with st.spinner("Fetching PR coverage data..."):
        pr_coverage = get_pr_coverage(pr_info)

    with st.spinner("Fetching develop branch coverage data..."):
        develop_coverage = get_latest_develop_coverage()

    if pr_coverage and develop_coverage:
        # Display the comparison
        display_pr_coverage_comparison(pr_coverage, develop_coverage)
        # Stop execution to not show the regular app content
        st.stop()
    else:
        st.error("Could not fetch coverage data for comparison")
        st.stop()

# Check if a file was uploaded
if uploaded_file:
    with st.spinner("Processing uploaded coverage data..."):
        coverage_data, total_data = parse_vitest_coverage_json(uploaded_file)

        if coverage_data and total_data:
            st.success("Successfully parsed uploaded coverage file.")
            # Display detailed coverage information
            display_coverage_details(coverage_data, total_data)
            # Stop execution to not show the GitHub data
            st.stop()
        else:
            st.error("Failed to parse the uploaded coverage file.")


# Main app logic
with st.spinner("Fetching data..."):
    # If no file was uploaded or parsing failed, continue with GitHub data
    # Fetch workflow runs
    workflow_runs = fetch_workflow_runs(
        "js-tests.yml", limit=workflow_runs_limit, since=since_date
    )

    if not workflow_runs:
        st.warning("No workflow runs found for the specified criteria.")
        st.stop()

    # Process the data
    coverage_history = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, run in enumerate(workflow_runs):
        progress_bar.progress(
            (i + 1) / len(workflow_runs),
            text=f"Processing run {i + 1}/{len(workflow_runs)}: {run['head_sha'][:7]}",
        )

        coverage_data = get_coverage_data_from_artifact(run["id"])

        if coverage_data:
            coverage_history.append(
                {
                    "run_id": run["id"],
                    "commit_sha": run["head_sha"][:7],
                    "commit_url": f"https://github.com/streamlit/streamlit/commit/{run['head_sha']}",
                    "created_at": datetime.strptime(
                        run["created_at"], "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "lines_pct": coverage_data["lines_pct"],
                    "functions_pct": coverage_data["functions_pct"],
                    "branches_pct": coverage_data["branches_pct"],
                    "lines_total": coverage_data["lines_total"],
                    "lines_covered": coverage_data["lines_covered"],
                    "functions_total": coverage_data["functions_total"],
                    "functions_covered": coverage_data["functions_covered"],
                    "branches_total": coverage_data["branches_total"],
                    "branches_covered": coverage_data["branches_covered"],
                    "run_url": run["html_url"],
                }
            )

    progress_bar.empty()
    status_text.empty()

    # Create DataFrame
    if coverage_history:
        df = pd.DataFrame(coverage_history)
        df = df.sort_values("created_at")
    else:
        st.warning("No coverage data found in the workflow runs.")
        st.stop()

# Display metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Average Lines Coverage", f"{df['lines_pct'].mean():.2f}%")
with col2:
    st.metric("Average Functions Coverage", f"{df['functions_pct'].mean():.2f}%")
with col3:
    st.metric("Average Branches Coverage", f"{df['branches_pct'].mean():.2f}%")


# Create a Plotly figure for the coverage over time
fig_coverage = px.line(
    df,
    x="created_at",
    y=["lines_pct", "functions_pct", "branches_pct"],
    title="Code Coverage Over Time",
    labels={"created_at": "Date", "value": "Coverage %", "variable": "Metric"},
    markers=True,
)

# Map variable names to display names
fig_coverage.for_each_trace(
    lambda trace: trace.update(
        name={
            "lines_pct": "Lines",
            "functions_pct": "Functions",
            "branches_pct": "Branches",
        }.get(trace.name, trace.name)
    )
)

# Update hover information
fig_coverage.update_traces(
    hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Commit:</b> %{customdata[0]}<br><b>Coverage:</b> %{y:.2f}%",
    customdata=df[["commit_sha"]],
)

# Update layout
fig_coverage.update_layout(
    xaxis_title="Date",
    yaxis_title="Coverage %",
    hovermode="closest",
)

# Display the chart
st.plotly_chart(
    fig_coverage,
    use_container_width=True,
    theme="streamlit",
)

# Create a multi-line chart for statements with Plotly
df_melted = pd.melt(
    df,
    id_vars=["created_at", "commit_sha"],
    value_vars=[
        "lines_total",
        "lines_covered",
        "functions_total",
        "functions_covered",
        "branches_total",
        "branches_covered",
    ],
    var_name="Metric",
    value_name="Value",
)

fig_metrics = px.line(
    df_melted,
    x="created_at",
    y="Value",
    color="Metric",
    title="Coverage Metrics Over Time",
    labels={"created_at": "Date", "Value": "Count", "Metric": "Metric"},
    markers=True,
)

# Map metric names to display names
fig_metrics.for_each_trace(
    lambda trace: trace.update(
        name={
            "lines_total": "Lines Total",
            "lines_covered": "Lines Covered",
            "functions_total": "Functions Total",
            "functions_covered": "Functions Covered",
            "branches_total": "Branches Total",
            "branches_covered": "Branches Covered",
        }.get(trace.name, trace.name)
    )
)

# Add hover information
fig_metrics.update_traces(
    hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Commit:</b> %{customdata[0]}<br><b>Value:</b> %{y}<br><b>Metric:</b> %{customdata[1]}",
    customdata=df_melted[["commit_sha", "Metric"]],
)

# Update layout
fig_metrics.update_layout(
    xaxis_title="Date",
    yaxis_title="Count",
    hovermode="closest",
)

st.plotly_chart(fig_metrics, use_container_width=True, theme="streamlit")

# Create a table with the data
st.subheader("Coverage History")

st.caption(
    ":material/keyboard_arrow_down: Select a row to view the detailed coverage information for that run."
)
# Create a dataframe for the coverage history with row selection
coverage_history_df = df[
    [
        "created_at",
        "commit_sha",
        "lines_pct",
        "functions_pct",
        "branches_pct",
        "lines_total",
        "lines_covered",
        "run_id",
        "run_url",
        "commit_url",
    ]
]
coverage_history_df = coverage_history_df.sort_values("created_at", ascending=False)

# Calculate coverage change percentage
coverage_history_df["lines_coverage_change"] = coverage_history_df["lines_pct"].diff(-1)

# Add HTML report URLs to the dataframe
coverage_history_df["html_report_url"] = coverage_history_df["run_id"].apply(
    get_html_report_url
)

# Display the dataframe with row selection enabled
df_selection = st.dataframe(
    coverage_history_df,
    use_container_width=True,
    column_config={
        "created_at": st.column_config.DatetimeColumn("Date", format="distance"),
        "commit_sha": st.column_config.TextColumn("Commit"),
        "lines_pct": st.column_config.ProgressColumn(
            "Lines Coverage %",
            help="Percentage of lines covered by tests",
            format="%.1f%%",
            min_value=0,
            max_value=100,
        ),
        "functions_pct": st.column_config.ProgressColumn(
            "Functions Coverage %",
            help="Percentage of functions covered by tests",
            format="%.1f%%",
            min_value=0,
            max_value=100,
        ),
        "branches_pct": st.column_config.ProgressColumn(
            "Branches Coverage %",
            help="Percentage of branches covered by tests",
            format="%.1f%%",
            min_value=0,
            max_value=100,
        ),
        "lines_coverage_change": st.column_config.NumberColumn(
            "Coverage Change",
            help="Change in lines coverage percentage compared to the previous commit",
            format="%.2f%%",
        ),
        "lines_total": st.column_config.NumberColumn("Total Lines"),
        "lines_covered": st.column_config.NumberColumn("Covered Lines"),
        "run_url": st.column_config.LinkColumn("Workflow Run", display_text="View Run"),
        "commit_url": st.column_config.LinkColumn(
            "Commit",
            display_text="https://github.com/streamlit/streamlit/commit/([a-f0-9]{7}).*",
        ),
        "html_report_url": st.column_config.LinkColumn(
            "HTML Report",
            display_text="Download",
            help="Download the full HTML coverage report",
        ),
    },
    hide_index=True,
    column_order=[
        "created_at",
        "lines_total",
        "lines_covered",
        "lines_coverage_change",
        "lines_pct",
        "functions_pct",
        "branches_pct",
        "html_report_url",
        "commit_url",
        "run_url",
    ],
    on_select="rerun",
    selection_mode="single-row",
    key="coverage_history_df",
)

# Check if a row was selected from the dataframe
if df_selection.selection.rows:
    # Get the selected row index
    selected_row_index = df_selection.selection.rows[0]
    selected_row = coverage_history_df.iloc[selected_row_index]

    selected_run_id = selected_row["run_id"]

    # Fetch artifacts for the selected run
    artifacts = fetch_artifacts(selected_run_id)

    coverage_json_artifact = None
    for artifact in artifacts:
        if artifact["name"] == "vitest_coverage_json":
            coverage_json_artifact = artifact
            break

    if coverage_json_artifact:
        # Download the artifact
        artifact_content = download_artifact(
            coverage_json_artifact["archive_download_url"]
        )

        if artifact_content:
            # Extract the coverage JSON file from the zip
            try:
                with ZipFile(BytesIO(artifact_content)) as zip_file:
                    file_list = zip_file.namelist()
                    # Find a JSON file that contains coverage data
                    json_file = next(
                        (f for f in file_list if f.endswith(".json")), None
                    )

                    if json_file:
                        with zip_file.open(json_file) as coverage_file:
                            coverage_data, total_data = parse_vitest_coverage_json(
                                coverage_file
                            )

                            if coverage_data and total_data:
                                # Display detailed coverage information
                                display_coverage_details(
                                    coverage_data,
                                    total_data,
                                    selected_row.get("html_report_url"),
                                    selected_run_id,
                                )
                            else:
                                st.error(
                                    "Failed to parse coverage data from the artifact."
                                )
            except Exception as e:
                st.error(f"Error extracting coverage data: {e}")
        else:
            st.error("Failed to download the coverage artifact.")
    else:
        st.warning("No coverage artifact found for this run.")
else:
    st.info("Select a row from the table above to view detailed coverage information.")
