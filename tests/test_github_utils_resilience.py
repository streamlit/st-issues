from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import requests

from app.utils import github_utils

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


class _FakeResponse:
    def __init__(
        self,
        *,
        status_code: int,
        payload: Any,
        text: str = "",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.headers = headers or {}

    def json(self) -> Any:
        return self._payload


class _FakeSecrets:
    def __init__(self, data: dict[str, Any] | None = None, *, raises: bool = False) -> None:
        self._data = data or {}
        self._raises = raises

    def get(self, key: str) -> Any:
        if self._raises:
            message = "secrets missing"
            raise RuntimeError(message)
        return self._data.get(key)


def test_get_headers_returns_accept_header_without_secrets(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(github_utils, "st", SimpleNamespace(secrets=_FakeSecrets(raises=True)))

    assert github_utils.get_headers() == {"Accept": "application/vnd.github.v3+json"}


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


def test_fetch_workflow_run_jobs_paginates(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_workflow_run_jobs.clear()
    pages = {
        1: {"jobs": [{"id": idx, "name": f"job-{idx}"} for idx in range(100)]},
        2: {"jobs": [{"id": 100, "name": "job-100"}]},
    }

    def fake_get(url: str, **kwargs: Any) -> _FakeResponse:
        assert "actions/runs/333/jobs" in url
        page = (kwargs.get("params") or {}).get("page", 1)
        return _FakeResponse(status_code=200, payload=pages[page])

    monkeypatch.setattr(github_utils, "get_headers", dict)
    monkeypatch.setattr(github_utils.requests, "get", fake_get)

    jobs = github_utils.fetch_workflow_run_jobs(333)
    assert len(jobs) == 101
    assert jobs[-1]["name"] == "job-100"


def test_fetch_workflow_run_annotations_paginates(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_workflow_run_annotations.clear()
    pages = {
        1: [{"message": f"warning {idx}"} for idx in range(100)],
        2: [{"message": "warning 100"}],
    }

    def fake_get(url: str, **kwargs: Any) -> _FakeResponse:
        assert "check-runs/99/annotations" in url
        page = (kwargs.get("params") or {}).get("page", 1)
        return _FakeResponse(status_code=200, payload=pages[page])

    monkeypatch.setattr(github_utils, "get_headers", dict)
    monkeypatch.setattr(github_utils.requests, "get", fake_get)

    annotations = github_utils.fetch_workflow_run_annotations(99)
    assert len(annotations) == 101
    assert annotations[-1]["message"] == "warning 100"


def test_fetch_dependabot_alerts_paginates_open_alerts(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_dependabot_alerts.clear()
    pages = [
        (
            [{"number": 1, "state": "open"}],
            '<https://api.github.com/repos/streamlit/streamlit/dependabot/alerts?state=open&page=2>; rel="next"',
        ),
        ([{"number": 2, "state": "open"}], ""),
    ]
    calls = {"count": 0}
    requested_urls: list[str] = []

    def fake_get(url: str, **_: Any) -> _FakeResponse:
        requested_urls.append(url)
        payload, link = pages[calls["count"]]
        calls["count"] += 1
        return _FakeResponse(status_code=200, payload=payload, headers={"Link": link})

    monkeypatch.setattr(github_utils, "get_headers", dict)
    monkeypatch.setattr(github_utils.requests, "get", fake_get)

    alerts = github_utils.fetch_dependabot_alerts("streamlit/streamlit")
    assert [alert["number"] for alert in alerts] == [1, 2]
    assert "state=open" in requested_urls[0]
    assert "per_page=100" in requested_urls[0]


def test_fetch_dependabot_alerts_forbidden_returns_empty(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_dependabot_alerts.clear()
    warnings: list[str] = []

    def ignore_error(_message: str) -> None:
        return None

    monkeypatch.setattr(
        github_utils,
        "st",
        SimpleNamespace(warning=warnings.append, error=ignore_error),
    )
    monkeypatch.setattr(github_utils, "get_headers", dict)
    monkeypatch.setattr(
        github_utils.requests,
        "get",
        lambda *_args, **_kwargs: _FakeResponse(status_code=403, payload={"message": "nope"}, text="nope"),
    )

    assert github_utils.fetch_dependabot_alerts() == []
    assert warnings
