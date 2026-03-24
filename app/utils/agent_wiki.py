from __future__ import annotations

import operator
import posixpath
import re
import shutil
import subprocess  # noqa: S404
import tempfile
from pathlib import Path
from typing import TypedDict
from urllib.parse import quote, urlsplit

import streamlit as st

WIKI_REPO = "streamlit/streamlit.wiki"
WIKI_BRANCH = "master"
WIKI_CLONE_URL = f"https://github.com/{WIKI_REPO}.git"
WIKI_LOCAL_CACHE_DIR = Path(tempfile.gettempdir()) / "st-issues-agent-wiki"
WIKI_LOCAL_REPO_DIR = WIKI_LOCAL_CACHE_DIR / "streamlit-streamlit.wiki"
WIKI_RAW_URL_PREFIX = "https://raw.githubusercontent.com/wiki/streamlit/streamlit"
WIKI_SOURCE_URL_PREFIX = f"https://github.com/{WIKI_REPO}/blob/{WIKI_BRANCH}"

ALLOWED_TOP_LEVEL_SECTIONS = {"pull-requests", "references"}
TEXT_DOCUMENT_EXTENSIONS = {".md", ".markdown", ".mdx", ".txt"}
MARKDOWN_EXTENSIONS = {".md", ".markdown", ".mdx"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
IMAGE_LINK_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
MARKDOWN_LINK_PATTERN = re.compile(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)")


class WikiDocument(TypedDict):
    path: str
    name: str
    parent: str
    folder: str
    section: str
    extension: str
    raw_url: str
    source_url: str
    is_markdown: bool
    is_image: bool


def _compact_error_text(text: str, max_chars: int = 280) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return f"{compact[:max_chars].rstrip()}..."


def _run_git_command(
    args: list[str],
    *,
    cwd: Path | None = None,
) -> tuple[str | None, str | None]:
    try:
        completed_process = subprocess.run(  # noqa: S603
            ["git", *args],  # noqa: S607
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None, "Git is not installed or not available on PATH."
    except OSError as exc:
        return None, f"Failed to run git {' '.join(args)}: {exc!s}"

    if completed_process.returncode != 0:
        stderr = completed_process.stderr.strip()
        stdout = completed_process.stdout.strip()
        details = stderr or stdout or "Unknown git error"
        return None, f"Git command failed (`git {' '.join(args)}`): {_compact_error_text(details)}"

    return completed_process.stdout, None


def _clone_wiki_repo(repo_dir: Path) -> str | None:
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    _, error = _run_git_command(
        [
            "clone",
            "--depth",
            "1",
            "--branch",
            WIKI_BRANCH,
            WIKI_CLONE_URL,
            str(repo_dir),
        ]
    )
    return error


def _update_wiki_repo(repo_dir: Path) -> str | None:
    _, fetch_error = _run_git_command(["fetch", "origin", WIKI_BRANCH, "--depth", "1"], cwd=repo_dir)
    if fetch_error:
        return fetch_error

    _, checkout_error = _run_git_command(["checkout", WIKI_BRANCH], cwd=repo_dir)
    if checkout_error:
        return checkout_error

    _, pull_error = _run_git_command(["pull", "--ff-only", "origin", WIKI_BRANCH], cwd=repo_dir)
    return pull_error


def _recreate_wiki_repo(repo_dir: Path) -> str | None:
    shutil.rmtree(repo_dir, ignore_errors=True)
    return _clone_wiki_repo(repo_dir)


def _get_extension(path: str) -> str:
    return posixpath.splitext(path)[1].lower()


def is_supported_document_path(path: str) -> bool:
    return _get_extension(path) in TEXT_DOCUMENT_EXTENSIONS


def is_markdown_path(path: str) -> bool:
    return _get_extension(path) in MARKDOWN_EXTENSIONS


def is_image_path(path: str) -> bool:
    return _get_extension(path) in IMAGE_EXTENSIONS


def build_wiki_raw_url(path: str) -> str:
    return f"{WIKI_RAW_URL_PREFIX}/{quote(path, safe='/')}"


def build_wiki_source_url(path: str) -> str:
    return f"{WIKI_SOURCE_URL_PREFIX}/{quote(path, safe='/')}"


def build_wiki_document_query_url(path: str) -> str:
    return f"?doc={quote(path, safe='')}"


def get_wiki_section(path: str) -> str:
    return path.split("/", 1)[0] if "/" in path else "(root)"


def is_browsable_wiki_path(path: str) -> bool:
    return get_wiki_section(path) in ALLOWED_TOP_LEVEL_SECTIONS


def get_wiki_folder(path: str) -> str:
    path_parts = [part for part in path.split("/") if part]
    if not path_parts:
        return "(root)"

    if path_parts[0] == "pull-requests" and len(path_parts) >= 2:
        return "/".join(path_parts[:2])

    parent = posixpath.dirname(path)
    return parent or "(root)"


def build_wiki_documents(paths: list[str]) -> list[WikiDocument]:
    documents: list[WikiDocument] = []
    for path in paths:
        if not is_browsable_wiki_path(path):
            continue

        documents.append(
            {
                "path": path,
                "name": posixpath.basename(path),
                "parent": posixpath.dirname(path),
                "folder": get_wiki_folder(path),
                "section": get_wiki_section(path),
                "extension": _get_extension(path),
                "raw_url": build_wiki_raw_url(path),
                "source_url": build_wiki_source_url(path),
                "is_markdown": is_markdown_path(path),
                "is_image": is_image_path(path),
            }
        )

    documents.sort(key=operator.itemgetter("section", "folder", "path"))
    return documents


@st.cache_data(ttl=60 * 10, show_spinner=False)
def get_synced_wiki_repo_path() -> tuple[str | None, str | None]:
    repo_dir = WIKI_LOCAL_REPO_DIR

    if not repo_dir.exists():
        clone_error = _clone_wiki_repo(repo_dir)
        if clone_error:
            return None, clone_error
    elif not (repo_dir / ".git").exists():
        recreate_error = _recreate_wiki_repo(repo_dir)
        if recreate_error:
            return None, recreate_error
    else:
        update_error = _update_wiki_repo(repo_dir)
        if update_error:
            recreate_error = _recreate_wiki_repo(repo_dir)
            if recreate_error:
                return None, recreate_error

    return str(repo_dir), None


@st.cache_data(ttl=60 * 10, show_spinner=False)
def fetch_wiki_documents() -> tuple[list[WikiDocument], str | None]:
    repo_path, error = get_synced_wiki_repo_path()
    if error or repo_path is None:
        return [], error

    repo_dir = Path(repo_path)
    document_paths = [
        file_path.relative_to(repo_dir).as_posix()
        for file_path in repo_dir.rglob("*")
        if file_path.is_file() and ".git" not in file_path.parts
    ]
    return build_wiki_documents(document_paths), None


def get_wiki_document_local_path(path: str) -> tuple[str | None, str | None]:
    repo_path, error = get_synced_wiki_repo_path()
    if error or repo_path is None:
        return None, error

    document_path = Path(repo_path) / Path(path)
    if not document_path.exists() or not document_path.is_file():
        return None, f"Document not found in local wiki clone: {path}"

    return str(document_path), None


@st.cache_data(ttl=60 * 10, max_entries=256, show_spinner=False)
def fetch_wiki_document_text(path: str) -> tuple[str | None, str | None]:
    local_path, error = get_wiki_document_local_path(path)
    if error or local_path is None:
        return None, error

    try:
        return Path(local_path).read_text(encoding="utf-8"), None
    except OSError as exc:
        return None, f"Failed reading wiki document {path}: {exc!s}"


def resolve_wiki_relative_path(current_path: str, target: str) -> str | None:
    stripped_target = target.strip()
    if not stripped_target or stripped_target.startswith("#"):
        return None

    parsed_target = urlsplit(stripped_target)
    if parsed_target.scheme or parsed_target.netloc:
        return None

    target_path = parsed_target.path
    if not target_path:
        return None

    if target_path.startswith("/"):
        resolved_path = posixpath.normpath(target_path.lstrip("/"))
    else:
        current_parent = posixpath.dirname(current_path)
        resolved_path = posixpath.normpath(posixpath.join(current_parent, target_path))

    if resolved_path in {"", "."} or resolved_path.startswith("../"):
        return None

    return resolved_path


def _extract_link_target(raw_target: str) -> str:
    cleaned_target = raw_target.strip()
    if cleaned_target.startswith("<") and cleaned_target.endswith(">"):
        return cleaned_target.removeprefix("<").removesuffix(">")
    return cleaned_target.split(" ", 1)[0].strip("'\"")


def rewrite_wiki_markdown(markdown_content: str, current_path: str) -> str:
    def replace_image(match: re.Match[str]) -> str:
        alt_text = match.group(1)
        target = _extract_link_target(match.group(2))
        resolved_path = resolve_wiki_relative_path(current_path, target)
        if resolved_path is None:
            return match.group(0)
        return f"![{alt_text}]({build_wiki_raw_url(resolved_path)})"

    rewritten_content = IMAGE_LINK_PATTERN.sub(replace_image, markdown_content)

    def replace_link(match: re.Match[str]) -> str:
        label = match.group(1)
        target = _extract_link_target(match.group(2))
        resolved_path = resolve_wiki_relative_path(current_path, target)
        if resolved_path is None:
            return match.group(0)
        return f"[{label}]({build_wiki_raw_url(resolved_path)})"

    return MARKDOWN_LINK_PATTERN.sub(replace_link, rewritten_content)


def extract_markdown_frontmatter(markdown_content: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER_PATTERN.match(markdown_content)
    if match is None:
        return {}, markdown_content

    frontmatter: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip("\"'")

    return frontmatter, markdown_content[match.end() :]


def extract_markdown_title(markdown_content: str) -> tuple[str | None, str]:
    lines = markdown_content.splitlines()
    content_without_title: list[str] = []
    title: str | None = None
    title_found = False

    for line in lines:
        if not title_found and line.startswith("# "):
            title = line[2:].strip()
            title_found = True
            continue
        content_without_title.append(line)

    return title, "\n".join(content_without_title)


def format_frontmatter_caption(frontmatter: dict[str, str]) -> str | None:
    if not frontmatter:
        return None

    preferred_keys = ("author", "created", "status")
    caption_parts = [f"{key.capitalize()}: {frontmatter[key]}" for key in preferred_keys if frontmatter.get(key)]

    if not caption_parts:
        return None

    return " | ".join(caption_parts)
