from __future__ import annotations

from typing import TYPE_CHECKING

import requests

from app.utils import markdown_rendering

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


class _FakeResponse:
    def __init__(self, *, status_code: int, payload: object) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> object:
        return self._payload


def test_sanitize_title_for_markdown_link_removes_problematic_characters() -> None:
    assert markdown_rendering.sanitize_title_for_markdown_link("Fix `[foo]` rendering") == "Fix (foo) rendering"


def test_fetch_issue_preview_details_returns_none_on_request_error(monkeypatch: MonkeyPatch) -> None:
    def fake_get(*args: object, **kwargs: object) -> _FakeResponse:
        message = "network down"
        raise requests.RequestException(message)

    monkeypatch.setattr(markdown_rendering.requests, "get", fake_get)

    issue_details, error = markdown_rendering.fetch_issue_preview_details("streamlit/streamlit", 123)

    assert issue_details is None
    assert error is None


def test_replace_issue_references_with_previews_formats_standalone_and_linked_issues(
    monkeypatch: MonkeyPatch,
) -> None:
    def fake_fetch_issue_preview_details(
        repo: str, issue_number: int
    ) -> tuple[markdown_rendering.IssuePreviewDetails, None]:
        return (
            {
                "title": f"Issue [{issue_number}] title",
                "url": f"https://github.com/{repo}/issues/{issue_number}",
                "state": "open",
                "number": issue_number,
                "upvotes": 7,
            },
            None,
        )

    monkeypatch.setattr(markdown_rendering, "fetch_issue_preview_details", fake_fetch_issue_preview_details)

    markdown_content = (
        "Standalone #123 and [#456](https://github.com/streamlit/streamlit/issues/456) should both render."
    )

    rewritten_content = markdown_rendering.replace_issue_references_with_previews(markdown_content)

    assert ":green[:material/circle:]" in rewritten_content
    assert ":gray[#123]" in rewritten_content
    assert ":gray[#456]" in rewritten_content
    assert "[Issue (123) title](https://github.com/streamlit/streamlit/issues/123)" in rewritten_content
    assert "[Issue (456) title](https://github.com/streamlit/streamlit/issues/456)" in rewritten_content


def test_replace_issue_references_with_previews_leaves_unknown_issue_as_plain_reference(
    monkeypatch: MonkeyPatch,
) -> None:
    def fake_fetch_issue_preview_details(
        repo: str, issue_number: int
    ) -> tuple[markdown_rendering.IssuePreviewDetails | None, None]:
        return None, None

    monkeypatch.setattr(markdown_rendering, "fetch_issue_preview_details", fake_fetch_issue_preview_details)

    assert markdown_rendering.replace_issue_references_with_previews("See #999.") == "See #999."
