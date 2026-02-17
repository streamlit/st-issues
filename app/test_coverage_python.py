import json
import pathlib
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any
from zipfile import ZipFile

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from app.utils.github_utils import (
    download_artifact,
    fetch_artifacts,
    fetch_pr_info,
    fetch_workflow_runs,
    fetch_workflow_runs_for_commit,
)
from app.utils.smokeshow import extract_and_upload_coverage_report

# Set page configuration
st.set_page_config(page_title="Python test coverage", page_icon="☂️", layout="wide")

# Get PR number from query parameters if available
query_params = st.query_params
pr_number = query_params.get("pr")

# Page title and description
title_row = st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center")
with title_row:
    st.title("☂️ Python test coverage")
    if st.button(":material/refresh: Refresh Data", type="tertiary"):
        fetch_workflow_runs.clear()
if pr_number is not None:
    st.caption(f"""
    Analyzing coverage for [PR #{pr_number}](https://github.com/streamlit/streamlit/pull/{pr_number})
    """)
    # Default values for PR mode
    since_date: datetime | None = None
    workflow_runs_limit = 1
    uploaded_file = None
else:
    st.caption("""
    This app shows test coverage trends (for Python) over time and allows you to analyze detailed coverage data for specific commits.
    """)

    time_period = st.sidebar.selectbox(
        "Time period",
        options=["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
        help="The time period to display coverage data for.  But it will still only load the last X workflow runs as defined by the slider below.",
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
        "Manual upload of coverage.json file",
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


def parse_coverage_json(coverage_file: Any) -> dict | None:
    """Parse a coverage.py JSON report file and return the data."""
    try:
        # Parse the JSON data
        coverage_data = json.load(coverage_file)

        # Create a dictionary to store coverage information
        coverage_info = {}

        # Process each file in the coverage data
        for file_path, file_data in coverage_data["files"].items():
            file_name = pathlib.Path(file_path).name

            # Get executed and missing lines directly from the file data
            executed_lines = file_data.get("executed_lines", [])
            missing_lines = file_data.get("missing_lines", [])

            # Calculate total lines (excluding comments and empty lines)
            total_lines = len(executed_lines) + len(missing_lines)

            # Calculate coverage percentage
            coverage_pct = (len(executed_lines) / total_lines * 100) if total_lines > 0 else 0

            # Store information
            coverage_info[file_path] = {
                "file_name": file_name,
                "file_path": file_path,
                "executed_lines": executed_lines,
                "missing_lines": missing_lines,
                "total_lines": total_lines,
                "coverage_pct": coverage_pct,
            }

        return coverage_info

    except json.JSONDecodeError:
        st.error("Invalid JSON file. Please ensure you're uploading a valid coverage.py JSON report.")
        return None
    except Exception as e:
        st.error(f"Error processing coverage data: {e!s}")
        return None


def extract_coverage_summary(coverage_data: dict) -> dict[str, Any]:
    """Extract summary statistics from coverage data."""
    total_lines = 0
    total_covered = 0
    total_files = len(coverage_data)

    for file_info in coverage_data.values():
        total_lines += file_info["total_lines"]
        total_covered += len(file_info["executed_lines"])

    coverage = (total_covered / total_lines) if total_lines > 0 else 0

    return {
        "total_files": total_files,
        "total_stmts": total_lines,
        "covered_stmts": total_covered,
        "total_miss": total_lines - total_covered,
        "coverage": coverage,
        "coverage_pct": coverage * 100,
    }


@st.cache_data(show_spinner=False)
def get_coverage_data_from_artifact(run_id: int) -> dict[str, Any] | None:
    """Get coverage data from the artifact of a workflow run."""
    artifacts = fetch_artifacts(run_id)

    coverage_json_artifact = None
    for artifact in artifacts:
        if artifact["name"] == "combined_coverage_json":
            coverage_json_artifact = artifact
            break

    if not coverage_json_artifact:
        return None

    # Download the artifact
    artifact_content = download_artifact(coverage_json_artifact["archive_download_url"])

    if not artifact_content:
        return None

    # Extract the coverage.json file from the zip
    try:
        with ZipFile(BytesIO(artifact_content)) as zip_file:
            with zip_file.open("coverage.json") as coverage_file:
                coverage_data = parse_coverage_json(coverage_file)
                if coverage_data:
                    return extract_coverage_summary(coverage_data)
    except Exception as e:
        st.error(f"Error extracting coverage data: {e}")

    return None


@st.cache_data(show_spinner=False)
def get_html_report_url(run_id: int) -> str | None:
    """Get the download URL for the HTML coverage report artifact."""
    artifacts = fetch_artifacts(run_id)

    html_report_artifact = None
    for artifact in artifacts:
        if artifact["name"] == "combined_coverage_report":
            html_report_artifact = artifact
            break

    if html_report_artifact:
        # Transform API URL to non-API GitHub URL format
        # From: https://api.github.com/repos/streamlit/streamlit/actions/artifacts/12345678/zip
        # To: https://github.com/streamlit/streamlit/actions/runs/12345678/artifacts/12345678
        artifact_id = html_report_artifact["id"]
        return f"https://github.com/streamlit/streamlit/actions/runs/{run_id}/artifacts/{artifact_id}"

    return None


def display_coverage_details(
    coverage_data: dict, html_report_url: str | None = None, run_id: int | None = None
) -> None:
    """Display detailed coverage information."""
    # Convert coverage data to DataFrame for easier manipulation
    coverage_df = pd.DataFrame(
        [
            {
                "Filename": info["file_name"],
                "Path": info["file_path"],
                "Lines Covered": len(info["executed_lines"]),
                "Lines Missed": len(info["missing_lines"]),
                "Lines Uncovered": len(info["missing_lines"]),
                "Total Lines": info["total_lines"],
                # "Coverage": round(info["coverage"], 2),
                "Coverage %": round(info["coverage_pct"], 2),
            }
            for _, info in coverage_data.items()
        ]
    )

    # Check if we have any data
    if len(coverage_df) == 0:
        st.warning("No coverage data found in the uploaded file.")
        return

    # Calculate overall statistics
    total_lines = coverage_df["Total Lines"].sum()
    total_covered = coverage_df["Lines Covered"].sum()
    overall_coverage = (total_covered / total_lines * 100) if total_lines > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Files", len(coverage_df))
    with col2:
        st.metric("Total Lines", total_lines)
    with col3:
        st.metric("Overall Coverage", f"{overall_coverage:.2f}%")

    # Create a gauge chart for overall coverage
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=overall_coverage,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Overall Coverage"},
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
                    "value": overall_coverage,
                },
            },
        )
    )

    st.plotly_chart(fig, width="stretch")

    # Display file-level coverage
    st.header("File Coverage Details")

    # Sort by coverage percentage (ascending)
    coverage_df = coverage_df.sort_values("Coverage %", ascending=False)

    # Create GitHub links for the Path column
    coverage_df["File"] = coverage_df["Path"].apply(
        lambda x: f"https://github.com/streamlit/streamlit/tree/develop/lib/{x}"
    )

    # Display the dataframe with coverage information and GitHub links
    file_coverage_selection = st.dataframe(
        coverage_df,
        column_config={
            "Coverage %": st.column_config.ProgressColumn(
                "Coverage %",
                help="Percentage of lines covered by tests",
                format="%f%%",
                min_value=0,
                max_value=100,
            ),
            "Lines Uncovered": st.column_config.NumberColumn("Lines Uncovered"),
            "File": st.column_config.LinkColumn(
                "File",
                help="View file in GitHub repository",
                display_text="https://github.com/streamlit/streamlit/tree/develop/lib/streamlit/(.*)",
                pinned=True,
            ),
        },
        hide_index=True,
        column_order=[
            "File",
            "Lines Covered",
            "Lines Uncovered",
            "Lines Missed",
            "Total Lines",
            "Coverage %",
        ],
        on_select="rerun",
        selection_mode="single-row",
        key="file_coverage_selection",
    )

    # Check if a file was selected
    if file_coverage_selection["selection"] and file_coverage_selection["selection"]["rows"]:
        selected_file_index = file_coverage_selection["selection"]["rows"][0]
        selected_file_path = coverage_df.iloc[selected_file_index]["Path"]
        selected_file_name = coverage_df.iloc[selected_file_index]["Filename"]

        # Get the coverage data for the selected file
        selected_file_data = coverage_data[selected_file_path]

        # Create JSON data for the selected file
        single_file_json = {
            "meta": {
                "version": "7.3.2",
                "timestamp": datetime.now().isoformat(),
                "show_contexts": False,
                "relative_files": True,
            },
            "files": {
                selected_file_path: {
                    "executed_lines": selected_file_data["executed_lines"],
                    "missing_lines": selected_file_data["missing_lines"],
                    "excluded_lines": [],
                    "summary": {
                        "covered_lines": len(selected_file_data["executed_lines"]),
                        "num_statements": selected_file_data["total_lines"],
                        "percent_covered": selected_file_data["coverage_pct"],
                        "percent_covered_display": f"{selected_file_data['coverage_pct']:.2f}",
                        "missing_lines": len(selected_file_data["missing_lines"]),
                        "excluded_lines": 0,
                    },
                }
            },
            "totals": {
                "covered_lines": len(selected_file_data["executed_lines"]),
                "num_statements": selected_file_data["total_lines"],
                "percent_covered": selected_file_data["coverage_pct"],
                "percent_covered_display": f"{selected_file_data['coverage_pct']:.2f}",
                "missing_lines": len(selected_file_data["missing_lines"]),
                "excluded_lines": 0,
            },
        }

        # Create download button
        st.download_button(
            label=f":material/download: Download coverage data for {selected_file_name}",
            data=json.dumps(single_file_json, indent=2),
            file_name=f"coverage_{selected_file_name}.json",
            mime="application/json",
            key="download_single_file_coverage",
        )

    col1, col2 = st.columns(2)
    # Add HTML report download button if URL is available
    if html_report_url:
        col1.link_button(
            label=":material/download: Download HTML Coverage Report",
            url=html_report_url,
            width="stretch",
        )
    if run_id and col2.button(":material/preview: View PR Report", width="stretch"):
        display_coverage_report_dialog(run_id=run_id)

    # Create a horizontal bar chart for file coverage
    if len(coverage_df) > 0:
        # Create a treemap visualization
        st.subheader("Coverage Treemap")

        # Add a size column for the treemap (using total lines)
        treemap_df = coverage_df.copy()

        # Extract directory structure
        treemap_df["Directory"] = treemap_df["Path"].apply(lambda x: pathlib.Path(x).parent.name or "root")

        fig = px.treemap(
            treemap_df,
            path=["Directory", "Filename"],
            values="Total Lines",
            color="Coverage %",
            color_continuous_scale=["red", "orange", "green"],
            range_color=[0, 100],
            hover_data=["Lines Covered", "Lines Missed", "Total Lines"],
        )

        st.plotly_chart(fig, width="stretch")

        st.subheader("Coverage by File")

        # Limit to top 20 files if there are many
        display_df = coverage_df.sort_values("Coverage %", ascending=True)
        if len(coverage_df) > 20:
            display_df = display_df.head(20)
            st.info("Showing only the 20 files with the lowest coverage. Use the table above to see all files.")

        fig = px.bar(
            display_df,
            y="Filename",
            x="Coverage %",
            orientation="h",
            color="Coverage %",
            color_continuous_scale=["red", "orange", "green"],
            range_color=[0, 100],
            labels={
                "Coverage %": "Coverage Percentage",
                "Filename": "Filename",
            },
        )

        fig.update_layout(yaxis={"categoryorder": "total descending"})
        st.plotly_chart(fig, width="stretch")

        # Display coverage distribution
        st.subheader("Coverage Distribution of Files")

        # Create coverage bins
        bins = [0, 20, 40, 60, 80, 100]
        labels = ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"]

        coverage_df["Coverage Range"] = pd.cut(
            coverage_df["Coverage %"],
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

        st.plotly_chart(fig, width="stretch")


def get_latest_develop_coverage() -> dict[str, Any] | None:
    """Get coverage data for the latest successful workflow run on develop."""
    # Fetch the latest successful workflow run on develop
    latest_runs = fetch_workflow_runs("python-tests.yml", limit=1)
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
        "total_stmts": coverage_data["total_stmts"],
        "total_miss": coverage_data["total_miss"],
        "covered_stmts": coverage_data["covered_stmts"],
        "coverage": coverage_data["coverage"],
        "coverage_pct": coverage_data["coverage_pct"],
        "run_url": latest_run["html_url"],
    }


def get_pr_coverage(pr_info: dict[str, Any]) -> dict[str, Any] | None:
    """Get coverage data for a PR's head commit."""
    head_sha = pr_info["head"]["sha"]
    # Fetch workflow runs for this commit
    pr_runs = fetch_workflow_runs_for_commit(head_sha, "python-tests.yml")

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
        "total_stmts": coverage_data["total_stmts"],
        "total_miss": coverage_data["total_miss"],
        "covered_stmts": coverage_data["covered_stmts"],
        "coverage": coverage_data["coverage"],
        "coverage_pct": coverage_data["coverage_pct"],
        "run_url": pr_run["html_url"],
    }


@st.cache_data(show_spinner=False)
def deploy_coverage_report(run_id: int) -> str | None:
    """Deploy the HTML coverage report to smokeshow."""
    # Fetch artifacts
    artifacts = fetch_artifacts(run_id)

    html_report_artifact = None
    for artifact in artifacts:
        if artifact["name"] == "combined_coverage_report":
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
def display_coverage_report_dialog(run_id: int) -> None:
    """Download, extract, upload and display the HTML coverage report in an iframe."""
    # Download the artifact
    with st.spinner("Downloading and deploying the coverage report..."):
        report_url = deploy_coverage_report(run_id)
        if not report_url:
            st.error("Failed to process the HTML coverage report.")
            return
        st.caption(f"[Open fullscreen :material/open_in_new:]({report_url})")
        # Display the iframe in a dialog
        components.iframe(report_url, height=600, scrolling=True)


def display_pr_coverage_comparison(pr_coverage: dict[str, Any], develop_coverage: dict[str, Any]) -> None:
    """Display a comparison of PR coverage against develop branch coverage."""
    st.subheader("PR Coverage Comparison")

    # Calculate coverage changes
    coverage_change = pr_coverage["coverage_pct"] - develop_coverage["coverage_pct"]
    total_stmts_change = pr_coverage["total_stmts"] - develop_coverage["total_stmts"]
    total_miss_change = pr_coverage["total_miss"] - develop_coverage["total_miss"]

    # Determine if changes are positive or negative
    coverage_delta = "+" if coverage_change >= 0 else ""
    stmts_delta = "+" if total_stmts_change >= 0 else ""
    miss_delta = "" if total_miss_change <= 0 else "+"  # Inverted logic for misses (less is better)

    # Create comparison columns
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Coverage",
            f"{pr_coverage['coverage_pct']:.2f}%",
            f"{coverage_delta}{coverage_change:.2f}%",
            delta_color="normal" if coverage_change >= 0 else "inverse",
        )

    with col2:
        st.metric(
            "Total Statements",
            f"{pr_coverage['total_stmts']}",
            f"{stmts_delta}{total_stmts_change}",
            delta_color="off",  # Neutral color as this is informational
        )

    with col3:
        st.metric(
            "Missed Statements",
            f"{pr_coverage['total_miss']}",
            f"{miss_delta}{total_miss_change}",
            delta_color="inverse" if total_miss_change <= 0 else "normal",
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
                label=":material/download: Download PR Coverage Report",
                url=pr_html_report_url,
                width="stretch",
            )
            if st.button(":material/preview: View PR Report", width="stretch"):
                display_coverage_report_dialog(pr_coverage["run_id"])

    with col2:
        if develop_html_report_url:
            st.link_button(
                label=":material/download: Download Develop Coverage Report",
                url=develop_html_report_url,
                width="stretch",
            )
            if st.button(":material/preview: View Develop Report", width="stretch"):
                display_coverage_report_dialog(develop_coverage["run_id"])

    # Get detailed coverage data for both PR and develop
    pr_artifact_content = None
    develop_artifact_content = None

    # Fetch artifacts for PR
    pr_artifacts = fetch_artifacts(pr_coverage["run_id"])
    pr_coverage_json_artifact = next((a for a in pr_artifacts if a["name"] == "combined_coverage_json"), None)
    if pr_coverage_json_artifact:
        pr_artifact_content = download_artifact(pr_coverage_json_artifact["archive_download_url"])

    # Fetch artifacts for develop
    develop_artifacts = fetch_artifacts(develop_coverage["run_id"])
    develop_coverage_json_artifact = next((a for a in develop_artifacts if a["name"] == "combined_coverage_json"), None)
    if develop_coverage_json_artifact:
        develop_artifact_content = download_artifact(develop_coverage_json_artifact["archive_download_url"])

    # If we have both artifacts, show a detailed file-by-file comparison
    if pr_artifact_content and develop_artifact_content:
        # Extract the coverage.json files from the zips
        pr_coverage_data: dict | None = {}
        develop_coverage_data: dict | None = {}

        try:
            with ZipFile(BytesIO(pr_artifact_content)) as zip_file:
                with zip_file.open("coverage.json") as coverage_file:
                    pr_coverage_data = parse_coverage_json(coverage_file)

            with ZipFile(BytesIO(develop_artifact_content)) as zip_file:
                with zip_file.open("coverage.json") as coverage_file:
                    develop_coverage_data = parse_coverage_json(coverage_file)

            if pr_coverage_data and develop_coverage_data:
                display_pr_detailed_comparison(pr_coverage_data, develop_coverage_data)
        except Exception as e:
            st.error(f"Error extracting coverage data: {e}")


def display_pr_detailed_comparison(pr_coverage_data: dict, develop_coverage_data: dict) -> None:
    """Display a detailed file-by-file comparison of PR coverage against develop coverage."""
    st.subheader("File-by-File Coverage Comparison")

    # Create DataFrames for PR and develop coverage
    pr_df = pd.DataFrame(
        [
            {
                "Filename": info["file_name"],
                "Path": file_path,
                "PR Coverage %": round(info["coverage_pct"], 2),
                "PR Lines Covered": len(info["executed_lines"]),
                "PR Lines Missed": len(info["missing_lines"]),
                "PR Total Lines": info["total_lines"],
            }
            for file_path, info in pr_coverage_data.items()
        ]
    )

    develop_df = pd.DataFrame(
        [
            {
                "Filename": info["file_name"],
                "Path": file_path,
                "Develop Coverage %": round(info["coverage_pct"], 2),
                "Develop Lines Covered": len(info["executed_lines"]),
                "Develop Lines Missed": len(info["missing_lines"]),
                "Develop Total Lines": info["total_lines"],
            }
            for file_path, info in develop_coverage_data.items()
        ]
    )

    # Merge the DataFrames on Path
    merged_df = pr_df.merge(
        develop_df,
        on=["Path", "Filename"],
        how="outer",
        suffixes=("_pr", "_develop"),
    ).fillna(0)

    # Calculate coverage changes
    merged_df["Coverage Change"] = merged_df["PR Coverage %"] - merged_df["Develop Coverage %"]
    merged_df["Lines Covered Change"] = merged_df["PR Lines Covered"] - merged_df["Develop Lines Covered"]
    merged_df["Lines Missed Change"] = merged_df["PR Lines Missed"] - merged_df["Develop Lines Missed"]
    merged_df["Total Lines Change"] = merged_df["PR Total Lines"] - merged_df["Develop Total Lines"]

    # Flag new and removed files
    merged_df["Status"] = "-"
    merged_df.loc[merged_df["Develop Total Lines"] == 0, "Status"] = "New"
    merged_df.loc[merged_df["PR Total Lines"] == 0, "Status"] = "Removed"

    # Create GitHub links for the Path column
    merged_df["File"] = merged_df["Path"].apply(
        lambda x: f"https://github.com/streamlit/streamlit/tree/develop/lib/{x}"
    )

    # Sort by coverage change
    merged_df = merged_df.sort_values("Coverage Change", ascending=True)

    # Display the dataframe
    st.dataframe(
        merged_df,
        column_config={
            "PR Coverage %": st.column_config.ProgressColumn(
                "PR Coverage %",
                format="%f%%",
                min_value=0,
                max_value=100,
            ),
            "Develop Coverage %": st.column_config.ProgressColumn(
                "Develop Coverage %",
                format="%f%%",
                min_value=0,
                max_value=100,
            ),
            "Coverage Change": st.column_config.NumberColumn(
                "Coverage Change",
                format="%+.2f%%",
            ),
            "Lines Covered Change": st.column_config.NumberColumn(
                "Lines Covered Change",
                format="%+d",
            ),
            "Lines Missed Change": st.column_config.NumberColumn(
                "Lines Missed Change",
                format="%+d",
            ),
            "Total Lines Change": st.column_config.NumberColumn(
                "Total Lines Change",
                format="%+d",
            ),
            "Status": st.column_config.TextColumn(
                "Status",
            ),
            "File": st.column_config.LinkColumn(
                "File",
                display_text="https://github.com/streamlit/streamlit/tree/develop/lib/streamlit/(.*)",
                pinned=True,
            ),
        },
        hide_index=True,
        column_order=[
            "File",
            "Coverage Change",
            "Lines Covered Change",
            "Lines Missed Change",
            "Total Lines Change",
            "PR Coverage %",
            "PR Lines Covered",
            "PR Lines Missed",
            "PR Total Lines",
            "Develop Coverage %",
            "Develop Lines Covered",
            "Develop Lines Missed",
            "Develop Total Lines",
            "Status",
        ],
    )

    # Create visualizations for changes
    st.subheader("Coverage Changes by File")

    # Filter out files with no changes and limit to top/bottom files
    changed_files = merged_df[merged_df["Coverage Change"] != 0].copy()
    if len(changed_files) > 20:
        # Get top 10 improved and top 10 decreased files
        improved = changed_files[changed_files["Coverage Change"] > 0].head(10)
        decreased = changed_files[changed_files["Coverage Change"] < 0].head(10)
        display_df = pd.concat([improved, decreased])
        st.info("Showing only the top 10 improved and top 10 decreased files. Use the table above to see all files.")
    else:
        display_df = changed_files

    if len(display_df) > 0:
        fig = px.bar(
            display_df,
            y="Filename",
            x="Coverage Change",
            orientation="h",
            color="Coverage Change",
            color_continuous_scale=["red", "white", "green"],
            color_continuous_midpoint=0,
            labels={
                "Coverage Change": "Coverage Change (%)",
                "Filename": "Filename",
            },
            title="Files with Coverage Changes",
        )

        fig.update_layout(yaxis={"categoryorder": "total descending"})
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No files with coverage changes found.")


# PR mode processing
if pr_number is not None:
    # Fetch PR info
    pr_info = fetch_pr_info(pr_number)
    if not pr_info:
        st.error(f"Could not fetch information for PR #{pr_number}")
        st.stop()

    # Get coverage for PR and develop
    with st.spinner("Fetching PR coverage data..."):
        pr_coverage = get_pr_coverage(pr_info)  # ty:ignore[invalid-argument-type]

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
        coverage_data = parse_coverage_json(uploaded_file)

        if coverage_data:
            st.success("Successfully parsed uploaded coverage file.")
            # Display detailed coverage information
            display_coverage_details(coverage_data)
            # Stop execution to not show the GitHub data
            st.stop()
        else:
            st.error("Failed to parse the uploaded coverage file.")


# Main app logic
with st.spinner("Fetching data..."):
    # If no file was uploaded or parsing failed, continue with GitHub data
    # Fetch workflow runs
    workflow_runs = fetch_workflow_runs("python-tests.yml", limit=workflow_runs_limit, since=since_date)

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
                    "created_at": datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                    "total_stmts": coverage_data["total_stmts"],
                    "total_miss": coverage_data["total_miss"],
                    "covered_stmts": coverage_data["covered_stmts"],
                    "coverage": coverage_data["coverage"],
                    "coverage_pct": coverage_data["coverage_pct"],
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

# Display metrics - show latest values with delta over the time period
# df is sorted by created_at ascending, so last row is latest, first row is oldest
latest = df.iloc[-1]
oldest = df.iloc[0]

# Calculate deltas (change from oldest to latest in the time range)
coverage_delta = latest["coverage_pct"] - oldest["coverage_pct"]
stmts_delta = latest["total_stmts"] - oldest["total_stmts"]
miss_delta = latest["total_miss"] - oldest["total_miss"]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Coverage",
        f"{latest['coverage_pct']:.2f}%",
        delta=f"{coverage_delta:+.2f}%",
        border=True,
    )
with col2:
    st.metric(
        "Total Statements",
        f"{latest['total_stmts']:,}",
        delta=f"{stmts_delta:+,}",
        delta_color="off",
        border=True,
    )
with col3:
    st.metric(
        "Missed Statements",
        f"{latest['total_miss']:,}",
        delta=f"{miss_delta:+,}",
        delta_color="inverse",
        border=True,
    )


# Create a Plotly figure for the coverage over time
fig_coverage = px.line(
    df,
    x="created_at",
    y="coverage_pct",
    title="Code Coverage Over Time",
    labels={"created_at": "Date", "coverage_pct": "Coverage %"},
    markers=True,
)

# Add hover information
fig_coverage.update_traces(
    hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Commit:</b> %{customdata[0]}<br><b>Coverage:</b> %{y:.2f}%<br><b>Total Statements:</b> %{customdata[1]}<br><b>Missed Statements:</b> %{customdata[2]}",
    customdata=df[["commit_sha", "total_stmts", "total_miss"]],
)

# Update layout
fig_coverage.update_layout(
    xaxis_title="Date",
    yaxis_title="Coverage %",
    hovermode="closest",
)

# Display the chart with selection
plotly_chart_state = st.plotly_chart(
    fig_coverage,
    width="stretch",
    theme="streamlit",
)

# Create a multi-line chart for statements with Plotly
df_melted = pd.melt(
    df,
    id_vars=["created_at", "commit_sha"],
    value_vars=["total_stmts", "covered_stmts", "total_miss"],
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

st.plotly_chart(fig_metrics, width="stretch", theme="streamlit")

# Create a table with the data
st.subheader("Coverage History")

st.caption(":material/keyboard_arrow_down: Select a row to view the detailed coverage information for that run.")
# Create a dataframe for the coverage history with row selection
coverage_history_df = df[
    [
        "created_at",
        "commit_sha",
        "coverage",
        "total_stmts",
        "total_miss",
        "run_id",
        "run_url",
        "commit_url",
    ]
]
coverage_history_df = coverage_history_df.sort_values("created_at", ascending=False)

# Calculate coverage change percentage
coverage_history_df["coverage_change"] = coverage_history_df["coverage"].diff(-1)

# Add HTML report URLs to the dataframe
coverage_history_df["html_report_url"] = coverage_history_df["run_id"].apply(get_html_report_url)

# Display the dataframe with row selection enabled
df_selection = st.dataframe(
    coverage_history_df,
    width="stretch",
    column_config={
        "created_at": st.column_config.DatetimeColumn("Date", format="distance"),
        "commit_sha": st.column_config.TextColumn("Commit"),
        "coverage": st.column_config.ProgressColumn("Coverage %", help="Percentage of lines covered by tests"),
        "coverage_change": st.column_config.NumberColumn(
            "Coverage Change",
            help="Change in coverage percentage compared to the previous commit",
            format="percent",
        ),
        "total_stmts": st.column_config.NumberColumn("Total Statements"),
        "total_miss": st.column_config.NumberColumn("Missed Statements"),
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
        "run_id": st.column_config.NumberColumn("Run ID"),
    },
    hide_index=True,
    column_order=[
        "created_at",
        "total_stmts",
        "total_miss",
        "coverage_change",
        "coverage",
        "html_report_url",
        "commit_url",
        "run_url",
    ],
    on_select="rerun",
    selection_mode="single-row",
    key="coverage_history_df",
)

# Check if a row was selected from the dataframe
if df_selection["selection"]["rows"]:
    # Get the selected row index
    selected_row_index = df_selection["selection"]["rows"][0]
    # Get the data from the selected row
    selected_run_id = coverage_history_df.iloc[selected_row_index]["run_id"]
    selected_commit = coverage_history_df.iloc[selected_row_index]["commit_sha"]
    selected_date = coverage_history_df.iloc[selected_row_index]["created_at"]
    selected_coverage = coverage_history_df.iloc[selected_row_index]["coverage"]
    selected_html_report_url = coverage_history_df.iloc[selected_row_index]["html_report_url"]

    # Fetch artifacts for the selected run
    artifacts = fetch_artifacts(selected_run_id)

    coverage_json_artifact = None
    for artifact in artifacts:
        if artifact["name"] == "combined_coverage_json":
            coverage_json_artifact = artifact
            break

    if coverage_json_artifact:
        # Download the artifact
        artifact_content = download_artifact(coverage_json_artifact["archive_download_url"])

        if artifact_content:
            # Extract the coverage.json file from the zip
            with ZipFile(BytesIO(artifact_content)) as zip_file:
                with zip_file.open("coverage.json") as coverage_file:
                    coverage_data = parse_coverage_json(coverage_file)

                    if coverage_data:
                        # Display detailed coverage information
                        display_coverage_details(coverage_data, selected_html_report_url, selected_run_id)
                    else:
                        st.error("Failed to parse coverage data from the artifact.")
        else:
            st.error("Failed to download the coverage artifact.")
    else:
        st.warning("No coverage artifact found for this run.")
else:
    st.info("Select a row from the table above to view detailed coverage information.")
