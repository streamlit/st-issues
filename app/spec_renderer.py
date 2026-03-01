import operator
import re

import requests
import streamlit as st

from app.utils.github_utils import (
    fetch_issue_payload,
    fetch_pull_request_files_payload,
    fetch_pull_request_payload,
    fetch_repo_file_text_at_ref,
    get_all_github_prs,
    get_headers,
)

st.set_page_config(page_title="Spec renderer", page_icon="🔧")


def fetch_open_prs() -> list[dict]:
    """Fetch open PRs from streamlit/streamlit repo."""
    return get_all_github_prs(state="open")


def filter_spec_prs(prs: list[dict]) -> list[dict]:
    """Filter PRs that start with [spec]."""
    spec_prs = []
    for pr in prs:
        title = pr.get("title", "")
        if title.lower().startswith("[spec]"):
            spec_prs.append(pr)
    return spec_prs


@st.cache_data(ttl=600)
def fetch_merged_specs() -> list[dict]:
    """Fetch list of merged spec folders from the specs directory on develop branch."""
    url = "https://api.github.com/repos/streamlit/streamlit/contents/specs"
    try:
        response = requests.get(url, headers=get_headers(), params={"ref": "develop"}, timeout=30)
        if response.status_code != 200:
            return []
        contents = response.json()
    except requests.RequestException:
        return []

    specs = []
    date_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")

    for item in contents:
        if item.get("type") != "dir":
            continue
        name = item.get("name", "")
        match = date_pattern.match(name)
        if match:
            date_str = match.group(1)
            feature_name = match.group(2).replace("-", " ").title()
            specs.append(
                {
                    "folder": name,
                    "date": date_str,
                    "title": feature_name,
                    "path": f"specs/{name}/product-spec.md",
                }
            )

    specs.sort(key=operator.itemgetter("date"), reverse=True)
    return specs


def fetch_merged_spec_content(spec_path: str) -> tuple[str | None, str | None]:
    """Fetch the content of a merged spec file from the develop branch."""
    return fetch_repo_file_text_at_ref("streamlit/streamlit", spec_path, "develop")


@st.cache_data(ttl=300)
def fetch_pr_files(pr_number: int) -> tuple[list[dict], str | None]:
    """Fetch files changed in a PR."""
    return fetch_pull_request_files_payload("streamlit/streamlit", pr_number)


def find_spec_markdown_file(files: list[dict]) -> str | None:
    """Find the markdown file in specs directory that was added or modified."""
    for file in files:
        filename = file.get("filename", "")
        status = file.get("status", "")

        # Look for markdown files in specs directory that were added or modified
        if filename.startswith("specs/") and filename.endswith(".md") and status in {"added", "modified"}:
            return filename
    return None


def fetch_markdown_content(filepath: str, pr_number: int) -> tuple[str | None, str | None]:
    """Fetch the content of a markdown file from a PR."""
    pr_data, pr_error = fetch_pull_request_payload("streamlit/streamlit", pr_number)
    if pr_error:
        return None, pr_error
    if not pr_data:
        return None, f"Pull request #{pr_number} not found."

    head_sha = pr_data["head"]["sha"]
    return fetch_repo_file_text_at_ref("streamlit/streamlit", filepath, head_sha)


def clean_spec_title(title: str) -> str:
    """Remove [spec] prefix from title."""
    # Remove [spec] (case insensitive) and any leading/trailing whitespace
    cleaned = re.sub(r"^\[spec\]\s*", "", title, flags=re.IGNORECASE)
    return cleaned.strip()


def replace_local_images_with_github_urls(markdown_content: str, pr_number: int, spec_file_path: str) -> str:
    """Replace local image references with GitHub raw URLs."""
    pr_data, pr_error = fetch_pull_request_payload("streamlit/streamlit", pr_number)
    if pr_error or not pr_data:
        return markdown_content

    head_sha = pr_data["head"]["sha"]

    # Get the directory of the spec file to resolve relative paths
    spec_dir = "/".join(spec_file_path.split("/")[:-1])  # Remove filename, keep directory

    # Pattern to match markdown images with local paths
    # Matches: ![alt text](./path/to/image.ext) or ![](./path/to/image.ext) or ![alt](path/to/image.ext)
    image_pattern = r"!\[([^\]]*)\]\((?!https?://)([^)]+)\)"

    def replace_image(match: re.Match) -> str:
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
            final_dir_parts = dir_parts[:-up_count] if up_count <= len(dir_parts) else []
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


@st.cache_data(ttl=300)
def fetch_issue_details(issue_number: int) -> tuple[dict | None, str | None]:
    """Fetch issue details from GitHub API."""
    issue_data, issue_error = fetch_issue_payload("streamlit/streamlit", issue_number)
    if issue_error:
        return None, issue_error
    if not issue_data:
        return None, None

    return {
        "title": issue_data["title"],
        "url": issue_data["html_url"],
        "state": issue_data["state"],
        "number": issue_data["number"],
        "upvotes": issue_data.get("reactions", {}).get("+1", 0),
    }, None


def sanitize_title_for_markdown_link(title: str) -> str:
    """Remove or escape markdown special characters from title for use in link text."""
    # Remove backticks which break markdown link syntax
    sanitized = title.replace("`", "")
    # Remove square brackets which interfere with link syntax
    sanitized = sanitized.replace("[", "(").replace("]", ")")
    return sanitized


def replace_issue_references_with_previews(markdown_content: str) -> str:
    """Replace issue references with styled previews."""
    # Pattern for issue links like [#12331](https://github.com/streamlit/streamlit/issues/12331)
    # Also handles optional trailing content in URL (query params, anchors)
    link_pattern = r"\[#(\d+)\]\(https://github\.com/streamlit/streamlit/issues/\d+[^)]*\)"

    # Pattern for standalone issue numbers like #1234
    # Must not be preceded by '[' and must not be followed by ']' or '('
    standalone_pattern = r"(?<!\[)#(\d+)(?![\]\(])"

    def create_issue_preview(issue_number: int) -> str:
        """Create a styled issue preview using only markdown features."""
        issue_details, _ = fetch_issue_details(issue_number)

        if not issue_details:
            return f"#{issue_number}"

        # Choose icon and color based on issue state
        if issue_details["state"] == "open":
            status_icon = ":green[:material/circle:]"
        else:
            status_icon = ":violet[:material/check_circle:]"

        # Sanitize and truncate title for use in markdown link
        title = sanitize_title_for_markdown_link(issue_details["title"])
        if len(title) > 50:
            title = title[:50] + "..."

        # Add upvotes badge
        upvotes = issue_details.get("upvotes", 0)
        upvotes_badge = f":orange-badge[{upvotes} :material/thumb_up:]"

        # Create preview using Streamlit's built-in markdown features
        # Format: :green[:material/circle:] :gray[#1234] [Issue title here](url) :orange-badge[123 :material/thumb_up:]
        preview = f"{status_icon} :gray[#{issue_details['number']}] [{title}]({issue_details['url']}) {upvotes_badge}"

        return preview

    def replace_standalone_issue(match: re.Match) -> str:
        issue_number = int(match.group(1))
        return create_issue_preview(issue_number)

    def replace_issue_link(match: re.Match) -> str:
        issue_number = int(match.group(1))
        return create_issue_preview(issue_number)

    # Replace issue links FIRST (before standalone), so we don't corrupt the link syntax
    updated_content = re.sub(link_pattern, replace_issue_link, markdown_content)

    # Then replace standalone issue references
    updated_content = re.sub(standalone_pattern, replace_standalone_issue, updated_content)

    return updated_content


def replace_github_mentions_with_links(markdown_content: str) -> str:
    """Replace GitHub username mentions with clickable links."""
    # Pattern for GitHub mentions like @username
    # Avoid matching email addresses by ensuring no dot after @
    mention_pattern = r"@([a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38})(?!\.[a-zA-Z])"

    def create_mention_link(match: re.Match) -> str:
        username = match.group(1)
        # Create a link to the GitHub profile
        return f"[@{username}](https://github.com/{username})"

    # Replace all GitHub mentions
    updated_content = re.sub(mention_pattern, create_mention_link, markdown_content)

    return updated_content


def extract_frontmatter(markdown_content: str) -> tuple[dict | None, str]:
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


def is_likely_github_username(name: str) -> bool:
    """Check if a string looks like a GitHub username."""
    if not name or len(name) > 39:
        return False
    # GitHub usernames: alphanumeric and hyphens, can't start/end with hyphen
    github_username_pattern = r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$"
    return bool(re.match(github_username_pattern, name))


def render_frontmatter_caption(frontmatter: dict) -> None:
    """Render frontmatter as caption."""
    if not frontmatter:
        return

    info_parts = []

    # Add author (with link if it's a GitHub mention or looks like a username)
    if "author" in frontmatter:
        author = frontmatter["author"].strip("\"'")  # Remove surrounding quotes
        if author.startswith("@"):
            username = author[1:]  # Remove @
            author_link = f"[@{username}](https://github.com/{username})"
            info_parts.append(f"By {author_link}")
        elif is_likely_github_username(author):
            # Treat as GitHub username even without @
            author_link = f"[@{author}](https://github.com/{author})"
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


def extract_title_and_content(markdown_content: str) -> tuple[str | None, str]:
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


def replace_local_images_with_github_urls_for_merged_spec(markdown_content: str, spec_file_path: str) -> str:
    """Replace local image references with GitHub raw URLs for merged specs on develop branch."""
    # Get the directory of the spec file to resolve relative paths
    spec_dir = "/".join(spec_file_path.split("/")[:-1])  # Remove filename, keep directory

    # Pattern to match markdown images with local paths
    image_pattern = r"!\[([^\]]*)\]\((?!https?://)([^)]+)\)"

    def replace_image(match: re.Match) -> str:
        alt_text = match.group(1)
        image_path = match.group(2)

        # Handle relative paths
        if image_path.startswith("./"):
            clean_path = image_path[2:]
            full_path = f"{spec_dir}/{clean_path}" if spec_dir else clean_path
        elif image_path.startswith("../"):
            dir_parts = spec_dir.split("/") if spec_dir else []
            path_parts = image_path.split("/")
            up_count = sum(1 for part in path_parts if part == "..")
            remaining_parts = [part for part in path_parts if part != ".."]
            final_dir_parts = dir_parts[:-up_count] if up_count <= len(dir_parts) else []
            full_path = "/".join(final_dir_parts + remaining_parts)
        else:
            full_path = f"{spec_dir}/{image_path}" if spec_dir else image_path

        # Create GitHub raw URL for develop branch
        github_url = f"https://raw.githubusercontent.com/streamlit/streamlit/develop/{full_path}"
        return f"![{alt_text}]({github_url})"

    return re.sub(image_pattern, replace_image, markdown_content)


def render_spec_content(
    markdown_content: str,
    spec_file_path: str,
    pr_number: int | None = None,
) -> None:
    """Render spec content with all transformations applied."""
    # Extract frontmatter
    frontmatter, content_without_frontmatter = extract_frontmatter(markdown_content)

    # Extract title and remaining content
    title, remaining_content = extract_title_and_content(content_without_frontmatter)

    # Render title if found
    if title:
        st.markdown(f"# {title}")

    # Render frontmatter as caption below title
    if frontmatter:
        render_frontmatter_caption(frontmatter)

    # Replace local image references with GitHub URLs
    if pr_number is not None:
        processed_content = replace_local_images_with_github_urls(remaining_content, pr_number, spec_file_path)
    else:
        processed_content = replace_local_images_with_github_urls_for_merged_spec(remaining_content, spec_file_path)

    # Replace issue references with styled previews
    processed_content = replace_issue_references_with_previews(processed_content)

    st.markdown(processed_content)


def render_open_spec_prs() -> None:
    """Render the open spec PRs tab."""
    # Get query parameters
    query_params = st.query_params
    pr_param = query_params.get("pr", None)

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

    # Determine default index based on query parameter
    default_index = None
    if pr_param:
        try:
            pr_number = int(pr_param)
            for i, (_option_key, pr) in enumerate(pr_options.items()):
                if pr["number"] == pr_number:
                    default_index = i
                    break
        except ValueError:
            pass

    selected_option = st.selectbox(
        "Select a spec PR:",
        options=list(pr_options.keys()),
        index=default_index,
        key="spec_selector",
    )

    if selected_option:
        selected_pr = pr_options[selected_option]
        pr_number = selected_pr["number"]

        # Only update query parameter if selection has changed
        if "last_selected_pr" not in st.session_state or st.session_state.last_selected_pr != pr_number:
            st.query_params["pr"] = str(pr_number)
            st.session_state.last_selected_pr = pr_number

        # Fetch PR files
        with st.spinner("Fetching PR files..."):
            pr_files, pr_files_error = fetch_pr_files(pr_number)
        if pr_files_error:
            if pr_files:
                st.warning("PR files were only partially loaded. Results may be incomplete.")
            else:
                st.error(pr_files_error)
                return

        if not pr_files:
            st.warning("No files found for this PR.")
            return

        # Find spec markdown file
        spec_file = find_spec_markdown_file(pr_files)

        if not spec_file:
            st.warning("No spec markdown file found in this PR.")
            st.info("Looking for markdown files in the `specs/` directory that were added or modified.")

            # Show all files for debugging
            with st.expander("All files in this PR"):
                for file in pr_files:
                    st.text(f"{file['status']}: {file['filename']}")
            return

        # Fetch and render markdown content
        with st.spinner("Fetching markdown content..."):
            markdown_content, markdown_error = fetch_markdown_content(spec_file, pr_number)
        if markdown_error:
            st.error(markdown_error)
            return

        if markdown_content:
            render_spec_content(markdown_content, spec_file, pr_number)
        else:
            st.error("Failed to fetch markdown content.")


def render_merged_specs() -> None:
    """Render the merged specs tab."""
    query_params = st.query_params
    spec_param = query_params.get("spec", None)

    merged_specs = fetch_merged_specs()

    if not merged_specs:
        st.info("No merged specs found in the repository.")
        return

    # Create selectbox options
    spec_options = {}
    for spec in merged_specs:
        label = f"{spec['date']} - {spec['title']}"
        spec_options[label] = spec

    # Determine default index based on query parameter
    default_index = None
    if spec_param:
        for i, spec in enumerate(merged_specs):
            if spec["folder"] == spec_param:
                default_index = i
                break

    selected_option = st.selectbox(
        "Select a merged spec:",
        options=list(spec_options.keys()),
        index=default_index,
        key="merged_spec_selector",
    )

    if selected_option:
        selected_spec = spec_options[selected_option]

        # Update query parameter
        if (
            "last_selected_spec" not in st.session_state
            or st.session_state.last_selected_spec != selected_spec["folder"]
        ):
            st.query_params["spec"] = selected_spec["folder"]
            st.session_state.last_selected_spec = selected_spec["folder"]

        # Fetch and render spec content
        with st.spinner("Fetching spec content..."):
            markdown_content, error = fetch_merged_spec_content(selected_spec["path"])

        if error:
            st.error(error)
            return

        if markdown_content:
            render_spec_content(markdown_content, selected_spec["path"])
        else:
            st.warning(f"Could not find `product-spec.md` in `{selected_spec['folder']}`.")


def main() -> None:
    title_row = st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center")
    with title_row:
        st.title("🔧 Spec renderer")
        if st.button(":material/refresh: Refresh Data", type="tertiary"):
            get_all_github_prs.clear()
            fetch_pr_files.clear()
            fetch_pull_request_payload.clear()
            fetch_repo_file_text_at_ref.clear()
            fetch_issue_payload.clear()
            fetch_merged_specs.clear()
    st.markdown("Read product specs from the Streamlit repo.")

    # Determine initial view from query params
    view_param = st.query_params.get("view")
    if view_param == "review" or "pr" in st.query_params:
        default_view = "In review"
    elif view_param == "approved" or "spec" in st.query_params:
        default_view = "Approved"
    else:
        default_view = "Approved"  # Default to approved specs

    view_options = ["In review", "Approved"]
    selected_view = st.segmented_control(
        "View",
        options=view_options,
        default=default_view,
        label_visibility="collapsed",
        width="stretch",
    )

    # Update query param when view changes and clean up conflicting params
    new_view_param = "approved" if selected_view == "Approved" else "review"
    if st.query_params.get("view") != new_view_param:
        st.query_params["view"] = new_view_param
        # Remove conflicting query params when switching views
        if new_view_param == "approved" and "pr" in st.query_params:
            del st.query_params["pr"]
        elif new_view_param == "review" and "spec" in st.query_params:
            del st.query_params["spec"]

    if selected_view == "In review":
        render_open_spec_prs()
    else:
        render_merged_specs()


main()
