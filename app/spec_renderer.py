import re
from typing import Dict, List, Optional

import requests
import streamlit as st

from app.utils.github_utils import get_all_github_prs, get_headers


def fetch_open_prs() -> List[Dict]:
    """Fetch open PRs from streamlit/streamlit repo."""
    return get_all_github_prs(state="open")


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
        response = requests.get(url, headers=get_headers(), timeout=100)
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
        pr_response = requests.get(pr_url, headers=get_headers(), timeout=100)
        pr_response.raise_for_status()
        pr_data = pr_response.json()
        head_sha = pr_data["head"]["sha"]

        # Fetch the file content from the PR's head commit
        content_url = (
            f"https://api.github.com/repos/streamlit/streamlit/contents/{filepath}"
        )
        params = {"ref": head_sha}

        content_response = requests.get(
            content_url, headers=get_headers(), params=params, timeout=100
        )
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


def replace_local_images_with_github_urls(
    markdown_content: str, pr_number: int, spec_file_path: str
) -> str:
    """Replace local image references with GitHub raw URLs."""
    # Get the PR details to find the head SHA
    pr_url = f"https://api.github.com/repos/streamlit/streamlit/pulls/{pr_number}"

    try:
        pr_response = requests.get(pr_url, headers=get_headers(), timeout=100)
        pr_response.raise_for_status()
        pr_data = pr_response.json()
        head_sha = pr_data["head"]["sha"]

        # Get the directory of the spec file to resolve relative paths
        spec_dir = "/".join(
            spec_file_path.split("/")[:-1]
        )  # Remove filename, keep directory

        # Pattern to match markdown images with local paths
        # Matches: ![alt text](./path/to/image.ext) or ![](./path/to/image.ext) or ![alt](path/to/image.ext)
        image_pattern = r"!\[([^\]]*)\]\((?!https?://)([^)]+)\)"

        def replace_image(match):
            alt_text = match.group(1)
            image_path = match.group(2)

            # Handle relative paths
            if image_path.startswith("./"):
                # Remove ./ and join with spec directory
                clean_path = image_path[2:]
                full_path = f"{spec_dir}/{clean_path}" if spec_dir else clean_path
            elif image_path.startswith("../"):
                # Handle parent directory references
                # Split spec_dir into parts and go up directories as needed
                dir_parts = spec_dir.split("/") if spec_dir else []
                path_parts = image_path.split("/")

                # Count how many ../ we have
                up_count = 0
                remaining_parts = []
                for part in path_parts:
                    if part == "..":
                        up_count += 1
                    else:
                        remaining_parts.append(part)

                # Go up the directory tree
                final_dir_parts = (
                    dir_parts[:-up_count] if up_count <= len(dir_parts) else []
                )
                full_path = "/".join(final_dir_parts + remaining_parts)
            else:
                # Assume it's relative to the spec directory
                full_path = f"{spec_dir}/{image_path}" if spec_dir else image_path

            # Create GitHub raw URL
            github_url = f"https://raw.githubusercontent.com/streamlit/streamlit/{head_sha}/{full_path}"

            return f"![{alt_text}]({github_url})"

        # Replace all local image references
        updated_content = re.sub(image_pattern, replace_image, markdown_content)
        return updated_content

    except requests.RequestException as e:
        st.warning(f"Failed to fetch PR details for image URL replacement: {e}")
        return markdown_content  # Return original content if we can't get PR details


@st.cache_data(ttl=300)
def fetch_issue_details(issue_number: int) -> Optional[Dict]:
    """Fetch issue details from GitHub API."""
    url = f"https://api.github.com/repos/streamlit/streamlit/issues/{issue_number}"

    try:
        response = requests.get(url, headers=get_headers(), timeout=100)
        response.raise_for_status()
        issue_data = response.json()
        return {
            "title": issue_data["title"],
            "url": issue_data["html_url"],
            "state": issue_data["state"],
            "number": issue_data["number"],
            "upvotes": issue_data.get("reactions", {}).get("+1", 0),
        }
    except requests.RequestException:
        return None


def replace_issue_references_with_previews(markdown_content: str) -> str:
    """Replace issue references with styled previews."""

    # Pattern for standalone issue numbers like #1234
    standalone_pattern = r"(?<!\[)#(\d+)(?!\])"

    # Pattern for issue links like [#12331](https://github.com/streamlit/streamlit/issues/12331)
    link_pattern = r"\[#(\d+)\]\(https://github\.com/streamlit/streamlit/issues/\d+\)"

    def create_issue_preview(issue_number: int) -> str:
        """Create a styled issue preview using only markdown features."""
        issue_details = fetch_issue_details(issue_number)

        if not issue_details:
            return f"#{issue_number}"

        # Choose badge content based on issue state
        if issue_details["state"] == "open":
            badge = ":green-badge[:material/circle: Open]"
        else:
            badge = ":violet-badge[:material/check_circle: Closed]"

        # Truncate title if too long
        title = issue_details["title"]
        if len(title) > 50:
            title = title[:50] + "..."

        # Add upvotes badge
        upvotes = issue_details.get("upvotes", 0)
        upvotes_badge = f":orange-badge[{upvotes} :material/thumb_up:]"

        # Create preview using Streamlit's built-in markdown features
        # Format: :gray[#1234] [Issue title here](url) :green-badge[:material/circle: Open] :orange-badge[123 :material/thumb_up:]
        preview = f":gray[#{issue_details['number']}] [{title}]({issue_details['url']}) {badge} {upvotes_badge}"

        return preview

    def replace_standalone_issue(match):
        issue_number = int(match.group(1))
        return create_issue_preview(issue_number)

    def replace_issue_link(match):
        issue_number = int(match.group(1))
        return create_issue_preview(issue_number)

    # Replace standalone issue references first
    updated_content = re.sub(
        standalone_pattern, replace_standalone_issue, markdown_content
    )

    # Then replace issue links
    updated_content = re.sub(link_pattern, replace_issue_link, updated_content)

    return updated_content


def replace_github_mentions_with_links(markdown_content: str) -> str:
    """Replace GitHub username mentions with clickable links."""

    # Pattern for GitHub mentions like @username
    # Avoid matching email addresses by ensuring no dot after @
    mention_pattern = (
        r"@([a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38})(?!\.[a-zA-Z])"
    )

    def create_mention_link(match):
        username = match.group(1)
        # Create a link to the GitHub profile
        return f"[@{username}](https://github.com/{username})"

    # Replace all GitHub mentions
    updated_content = re.sub(mention_pattern, create_mention_link, markdown_content)

    return updated_content


def extract_frontmatter(markdown_content: str) -> tuple[Optional[Dict], str]:
    """Extract YAML frontmatter from markdown content."""
    # Pattern to match frontmatter at the beginning of the document
    frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n"

    match = re.match(frontmatter_pattern, markdown_content, re.DOTALL)
    if not match:
        return None, markdown_content

    frontmatter_text = match.group(1)
    content_without_frontmatter = markdown_content[match.end() :]

    # Parse the frontmatter (simple key: value parsing)
    frontmatter = {}
    for line in frontmatter_text.strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip()

    return frontmatter, content_without_frontmatter


def render_frontmatter_caption(frontmatter: Dict) -> None:
    """Render frontmatter as caption."""
    if not frontmatter:
        return

    info_parts = []

    # Add author (with link if it's a GitHub mention)
    if "author" in frontmatter:
        author = frontmatter["author"]
        if author.startswith("@"):
            username = author[1:]  # Remove @
            author_link = f"[@{username}](https://github.com/{username})"
            info_parts.append(f"By {author_link}")
        else:
            info_parts.append(f"By {author}")

    # Add created date
    if "created" in frontmatter:
        info_parts.append(frontmatter["created"])

    # Add status
    if "status" in frontmatter:
        status = frontmatter["status"]
        # Add a colored badge with material icon for status
        if status.lower() == "draft":
            status_badge = f":orange-badge[:material/edit: {status}]"
        elif status.lower() == "approved":
            status_badge = f":green-badge[:material/check_circle: {status}]"
        elif status.lower() == "implemented":
            status_badge = f":blue-badge[:material/deployed_code: {status}]"
        else:
            status_badge = f":gray-badge[:material/help: {status}]"
        info_parts.append(status_badge)

    if info_parts:
        info_text = " • ".join(info_parts)
        st.caption(info_text)


def extract_title_and_content(markdown_content: str) -> tuple[Optional[str], str]:
    """Extract the first heading as title and return remaining content."""
    lines = markdown_content.split("\n")
    title = None
    content_lines = []
    title_found = False

    for line in lines:
        if not title_found and line.strip().startswith("# "):
            title = line.strip()[2:].strip()  # Remove '# ' and whitespace
            title_found = True
        elif title_found:
            content_lines.append(line)
        else:
            content_lines.append(line)

    remaining_content = "\n".join(content_lines)
    return title, remaining_content


def main():
    st.title("🔧 Spec Renderer")
    st.markdown(
        "Read product specs from the Streamlit repo. So far only supports PRs, not merged specs."
    )

    st.divider()

    # Fetch open PRs
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
        "Select a spec PR:", options=list(pr_options.keys()), index=None
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
            # Extract frontmatter
            frontmatter, content_without_frontmatter = extract_frontmatter(
                markdown_content
            )

            # Extract title and remaining content
            title, remaining_content = extract_title_and_content(
                content_without_frontmatter
            )

            # Render title if found
            if title:
                st.markdown(f"# {title}")

            # Render frontmatter as caption below title
            if frontmatter:
                render_frontmatter_caption(frontmatter)

            # Replace local image references with GitHub URLs
            processed_content = replace_local_images_with_github_urls(
                remaining_content, pr_number, spec_file
            )

            # Replace issue references with styled previews
            processed_content = replace_issue_references_with_previews(
                processed_content
            )

            # Replace GitHub mentions with clickable links
            processed_content = replace_github_mentions_with_links(processed_content)

            st.markdown(processed_content)
        else:
            st.error("Failed to fetch markdown content.")


if __name__ == "__main__":
    main()
