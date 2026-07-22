from __future__ import annotations

import streamlit as st

from app.utils.agent_wiki import (
    WikiDocument,
    extract_markdown_frontmatter,
    extract_markdown_title,
    fetch_wiki_document_text,
    fetch_wiki_documents,
    format_frontmatter_caption,
    get_synced_wiki_repo_path,
    get_wiki_document_local_path,
    rewrite_wiki_markdown,
)
from app.utils.markdown_rendering import replace_issue_references_with_previews

st.set_page_config(page_title="Agent wiki explorer", page_icon="📚")


def _render_markdown_document(document: WikiDocument, markdown_content: str) -> None:
    frontmatter, content_without_frontmatter = extract_markdown_frontmatter(markdown_content)
    title, content_without_title = extract_markdown_title(content_without_frontmatter)

    if title:
        st.markdown(f"## {title}")

    caption = format_frontmatter_caption(frontmatter)
    if caption:
        st.caption(caption)

    rewritten_content = rewrite_wiki_markdown(content_without_title, document["path"])
    enhanced_content = replace_issue_references_with_previews(rewritten_content)
    if enhanced_content.strip():
        st.markdown(enhanced_content)
    else:
        st.info("This document is empty.")


def _render_image_asset(document: WikiDocument) -> None:
    local_path, local_path_error = get_wiki_document_local_path(document["path"])
    if local_path_error:
        st.error(local_path_error)
        return
    if local_path is None:
        st.warning("The selected asset could not be loaded.")
        return
    st.image(local_path, caption=document["path"], width="stretch")


def _render_other_asset(document: WikiDocument) -> None:
    st.info("This asset is not rendered inline.")
    st.link_button("Open asset", document["raw_url"], width="content")


title_row = st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center")
with title_row:
    st.title("📚 Agent wiki explorer")
    if st.button(":material/refresh: Refresh data", type="tertiary"):
        get_synced_wiki_repo_path.clear()
        fetch_wiki_documents.clear()
        fetch_wiki_document_text.clear()

st.caption("Browse agent-generated docs from the public `streamlit/streamlit.wiki` repository.")

documents, documents_error = fetch_wiki_documents()
if documents_error and not documents:
    st.error(documents_error)
    st.stop()
if documents_error:
    st.warning(documents_error)

if not documents:
    st.info("No documents were found in the wiki repository.")
    st.stop()

selected_label = st.selectbox(
    "Wiki file",
    options=[document["path"] for document in documents],
    index=None,
    key="file",
    bind="query-params",
    label_visibility="collapsed",
    placeholder="Select a wiki file",
)
if selected_label is None:
    st.info("Select a wiki file to view it.")
    st.stop()

selected_document = next(document for document in documents if document["path"] == selected_label)

if selected_document["is_markdown"]:
    with st.spinner("Fetching document..."):
        document_text, document_error = fetch_wiki_document_text(selected_document["path"])
    if document_error:
        st.error(document_error)
        st.stop()
    if document_text is None:
        st.warning("The selected document could not be loaded.")
        st.stop()
    _render_markdown_document(selected_document, document_text)
elif selected_document["is_image"]:
    _render_image_asset(selected_document)
else:
    _render_other_asset(selected_document)
