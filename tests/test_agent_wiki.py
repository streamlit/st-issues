from app.utils.agent_wiki import (
    build_wiki_documents,
    build_wiki_raw_url,
    resolve_wiki_relative_path,
    rewrite_wiki_markdown,
)


def test_build_wiki_documents_includes_assets_in_supported_sections() -> None:
    documents = build_wiki_documents(
        [
            "pull-requests/12345/implementation-plan.md",
            "pull-requests/12345/notes.txt",
            "references/agent-guide.md",
            "pull-requests/12345/diagram.png",
            "AGENTS.md",
        ]
    )

    assert [document["path"] for document in documents] == [
        "pull-requests/12345/diagram.png",
        "pull-requests/12345/implementation-plan.md",
        "pull-requests/12345/notes.txt",
        "references/agent-guide.md",
    ]
    assert documents[0]["is_image"] is True
    assert documents[1]["folder"] == "pull-requests/12345"
    assert documents[3]["section"] == "references"


def test_resolve_wiki_relative_path_handles_parent_and_root_relative_targets() -> None:
    assert (
        resolve_wiki_relative_path(
            "pull-requests/12345/implementation-plan.md",
            "../12346/exploration.md#overview",
        )
        == "pull-requests/12346/exploration.md"
    )
    assert (
        resolve_wiki_relative_path(
            "pull-requests/12345/implementation-plan.md",
            "/references/agent-guide.md",
        )
        == "references/agent-guide.md"
    )
    assert resolve_wiki_relative_path("implementation-plan.md", "../outside.md") is None


def test_rewrite_wiki_markdown_rewrites_relative_assets_and_doc_links() -> None:
    markdown_content = """
![Diagram](diagram.png)
[Exploration](../12346/exploration.md)
[Source file](./data/schema.json)
[External](https://example.com)
""".strip()

    rewritten_content = rewrite_wiki_markdown(
        markdown_content,
        "pull-requests/12345/implementation-plan.md",
    )

    assert (
        "https://raw.githubusercontent.com/wiki/streamlit/streamlit/pull-requests/12345/diagram.png"
        in rewritten_content
    )
    assert build_wiki_raw_url("pull-requests/12346/exploration.md") in rewritten_content
    assert build_wiki_raw_url("pull-requests/12345/data/schema.json") in rewritten_content
    assert "[External](https://example.com)" in rewritten_content
