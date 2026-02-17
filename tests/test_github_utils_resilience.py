from __future__ import annotations

from typing import TYPE_CHECKING, Any

import requests

from app.utils import github_utils

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


class _FakeResponse:
    def __init__(self, *, status_code: int, payload: Any, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self) -> Any:
        return self._payload


def test_fetch_issue_comments_payload_keeps_partial_results_on_later_page_failure(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_issue_comments_payload.clear()

    calls = {"count": 0}

    def fake_get(url: str, **_: Any) -> _FakeResponse:
        calls["count"] += 1
        if calls["count"] == 1:
            payload = [{"id": idx, "body": f"comment {idx}"} for idx in range(1, 101)]
            return _FakeResponse(status_code=200, payload=payload)
        message = "network down"
        raise requests.RequestException(message)

    monkeypatch.setattr(github_utils, "get_headers", dict)
    monkeypatch.setattr(github_utils.requests, "get", fake_get)

    comments, error = github_utils.fetch_issue_comments_payload("streamlit/streamlit", 123)
    assert comments[0] == {"id": 1, "body": "comment 1"}
    assert len(comments) == 100
    assert error is not None


def test_fetch_issue_comments_payload_does_not_cache_errored_partial_results(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_issue_comments_payload.clear()

    calls = {"count": 0}

    def fake_get(url: str, **_: Any) -> _FakeResponse:
        calls["count"] += 1
        if calls["count"] % 2 == 1:
            payload = [{"id": idx, "body": f"comment {idx}"} for idx in range(1, 101)]
            return _FakeResponse(status_code=200, payload=payload)
        message = "network down"
        raise requests.RequestException(message)

    monkeypatch.setattr(github_utils, "get_headers", dict)
    monkeypatch.setattr(github_utils.requests, "get", fake_get)

    first_comments, first_error = github_utils.fetch_issue_comments_payload("streamlit/streamlit", 123)
    second_comments, second_error = github_utils.fetch_issue_comments_payload("streamlit/streamlit", 123)

    assert len(first_comments) == 100
    assert len(second_comments) == 100
    assert first_error is not None
    assert second_error is not None
    assert calls["count"] == 4


def test_fetch_issue_view_counts_keeps_partial_batches_on_failure(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_issue_view_counts.clear()

    calls = {"count": 0}

    def fake_get(url: str, **_: Any) -> _FakeResponse:
        calls["count"] += 1
        if calls["count"] == 1:
            payload = {
                "st-issue-1": {"views": 10},
                "st-issue-2": {"views": 20},
            }
            return _FakeResponse(status_code=200, payload=payload)
        message = "timeout"
        raise requests.RequestException(message)

    monkeypatch.setattr(github_utils.requests, "get", fake_get)

    view_counts, error = github_utils.fetch_issue_view_counts(tuple(range(1, 151)))
    assert view_counts[1] == 10
    assert view_counts[2] == 20
    assert error is not None


def test_fetch_issue_view_counts_does_not_cache_errored_partial_results(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_issue_view_counts.clear()

    calls = {"count": 0}

    def fake_get(url: str, **_: Any) -> _FakeResponse:
        calls["count"] += 1
        if calls["count"] % 2 == 1:
            payload = {
                "st-issue-1": {"views": 10},
                "st-issue-2": {"views": 20},
            }
            return _FakeResponse(status_code=200, payload=payload)
        message = "timeout"
        raise requests.RequestException(message)

    monkeypatch.setattr(github_utils.requests, "get", fake_get)

    first_view_counts, first_error = github_utils.fetch_issue_view_counts(tuple(range(1, 151)))
    second_view_counts, second_error = github_utils.fetch_issue_view_counts(tuple(range(1, 151)))

    assert first_view_counts[1] == 10
    assert second_view_counts[1] == 10
    assert first_error is not None
    assert second_error is not None
    assert calls["count"] == 4


def test_fetch_issue_view_counts_handles_non_dict_payload(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_issue_view_counts.clear()

    def fake_get(url: str, **_: Any) -> _FakeResponse:
        return _FakeResponse(status_code=200, payload=["unexpected"])

    monkeypatch.setattr(github_utils.requests, "get", fake_get)

    view_counts, error = github_utils.fetch_issue_view_counts((1, 2))
    assert view_counts == {}
    assert error is not None
