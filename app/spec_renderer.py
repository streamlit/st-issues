import re
from typing import Dict, List, Optional

import requests
import streamlit as st


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_open_prs() -> List[Dict]:
    """Fetch open PRs from streamlit/streamlit repo."""
    url = "https://api.github.com/repos/streamlit/streamlit/pulls"
    params = {"state": "open", "per_page": 100}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to fetch PRs: {e}")
        return []


def filter_spec_prs(prs: List[Dict]) -> List[Dict]:
    """Filter PRs that start with [spec]."""
    spec_prs = []
    for pr in prs:
        title = pr.get("title", "")
        if title.lower().startswith("[spec]"):
            spec_prs.append(pr)
    return spec_prs


@st.cache_data(ttl=300)
def fetch_pr_files(pr_number: int) -> List[Dict]:
    """Fetch files changed in a PR."""
    url = f"https://api.github.com/repos/streamlit/streamlit/pulls/{pr_number}/files"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to fetch PR files: {e}")
        return []


def find_spec_markdown_file(files: List[Dict]) -> Optional[str]:
    """Find the markdown file in specs directory that was added or modified."""
    for file in files:
        filename = file.get("filename", "")
        status = file.get("status", "")

        # Look for markdown files in specs directory that were added or modified
        if (
            filename.startswith("specs/")
            and filename.endswith(".md")
            and status in ["added", "modified"]
        ):
            return filename
    return None


@st.cache_data(ttl=300)
def fetch_markdown_content(filepath: str, pr_number: int) -> Optional[str]:
    """Fetch the content of a markdown file from a PR."""
    # Get the PR details to find the head SHA
    pr_url = f"https://api.github.com/repos/streamlit/streamlit/pulls/{pr_number}"

    try:
        pr_response = requests.get(pr_url)
        pr_response.raise_for_status()
        pr_data = pr_response.json()
        head_sha = pr_data["head"]["sha"]

        # Fetch the file content from the PR's head commit
        content_url = (
            f"https://api.github.com/repos/streamlit/streamlit/contents/{filepath}"
        )
        params = {"ref": head_sha}

        content_response = requests.get(content_url, params=params)
        content_response.raise_for_status()
        content_data = content_response.json()

        # Decode base64 content
        import base64

        content = base64.b64decode(content_data["content"]).decode("utf-8")
        return content

    except requests.RequestException as e:
        st.error(f"Failed to fetch markdown content: {e}")
        return None


def clean_spec_title(title: str) -> str:
    """Remove [spec] prefix from title."""
    # Remove [spec] (case insensitive) and any leading/trailing whitespace
    cleaned = re.sub(r"^\[spec\]\s*", "", title, flags=re.IGNORECASE)
    return cleaned.strip()


def main():
    st.title("🔧 Spec Renderer")
    st.markdown(
        "Read product specs from the Streamlit repo. So far only supports PRs, not merged specs."
    )

    st.divider()

    # Fetch open PRs
    with st.spinner("Fetching open PRs..."):
        all_prs = fetch_open_prs()

    if not all_prs:
        st.warning("No PRs found or failed to fetch PRs.")
        return

    # Filter for spec PRs
    spec_prs = filter_spec_prs(all_prs)

    if not spec_prs:
        st.info("No open spec PRs found.")
        return

    # Create selectbox with cleaned titles
    pr_options = {}
    for pr in spec_prs:
        cleaned_title = clean_spec_title(pr["title"])
        pr_options[f"#{pr['number']} - {cleaned_title}"] = pr

    if not pr_options:
        return

    selected_option = st.selectbox(
        "Select a spec PR:", options=list(pr_options.keys()), index=0
    )

    if selected_option:
        selected_pr = pr_options[selected_option]
        pr_number = selected_pr["number"]

        # Fetch PR files
        with st.spinner("Fetching PR files..."):
            pr_files = fetch_pr_files(pr_number)

        if not pr_files:
            st.warning("No files found for this PR.")
            return

        # Find spec markdown file
        spec_file = find_spec_markdown_file(pr_files)

        if not spec_file:
            st.warning("No spec markdown file found in this PR.")
            st.info(
                "Looking for markdown files in the `specs/` directory that were added or modified."
            )

            # Show all files for debugging
            with st.expander("All files in this PR"):
                for file in pr_files:
                    st.text(f"{file['status']}: {file['filename']}")
            return

        # Fetch and render markdown content
        with st.spinner("Fetching markdown content..."):
            markdown_content = fetch_markdown_content(spec_file, pr_number)

        if markdown_content:
            st.markdown(markdown_content)
        else:
            st.error("Failed to fetch markdown content.")


if __name__ == "__main__":
    main()
