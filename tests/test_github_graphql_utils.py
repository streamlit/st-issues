from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
import pytest
import requests
from requests.exceptions import ChunkedEncodingError

from app.utils import github_graphql_utils as gql

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


class _FakeResponse:
    def __init__(
        self,
        *,
        status_code: int,
        payload: Any = None,
        text: str = "",
        headers: dict[str, str] | None = None,
        json_error: bool = False,
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.headers = headers or {}
        self._json_error = json_error

    def json(self) -> Any:
        if self._json_error:
            message = "Expecting value"
            raise requests.exceptions.JSONDecodeError(message, "", 0)
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            message = f"{self.status_code} error"
            raise requests.HTTPError(message, response=self)


def _patch_graphql_runtime(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(gql, "get_graphql_headers", lambda: {"Accept": "application/json"})
    monkeypatch.setattr(gql.time, "sleep", lambda _seconds: None)


def test_run_graphql_query_retries_502_then_succeeds(monkeypatch: MonkeyPatch) -> None:
    _patch_graphql_runtime(monkeypatch)
    calls = {"count": 0}

    def fake_post(*_args: Any, **_kwargs: Any) -> _FakeResponse:
        calls["count"] += 1
        if calls["count"] == 1:
            return _FakeResponse(
                status_code=502,
                text="Bad Gateway",
                headers={"X-GitHub-Request-Id": "req-502"},
            )
        return _FakeResponse(status_code=200, payload={"data": {"ok": True}})

    monkeypatch.setattr(gql.requests, "post", fake_post)

    data = gql._run_graphql_query("query Ping { viewer { login } }", {"x": 1})

    assert data == {"ok": True}
    assert calls["count"] == 2


def test_run_graphql_query_retries_chunked_encoding_and_empty_200(monkeypatch: MonkeyPatch) -> None:
    _patch_graphql_runtime(monkeypatch)
    calls = {"count": 0}

    def fake_post(*_args: Any, **_kwargs: Any) -> _FakeResponse:
        calls["count"] += 1
        if calls["count"] == 1:
            message = "Response ended prematurely"
            raise ChunkedEncodingError(message)
        if calls["count"] == 2:
            return _FakeResponse(status_code=200, payload=None, text="", json_error=True)
        return _FakeResponse(status_code=200, payload={"data": {"viewer": {"login": "octocat"}}})

    monkeypatch.setattr(gql.requests, "post", fake_post)

    data = gql._run_graphql_query("query Viewer { viewer { login } }", {})

    assert data == {"viewer": {"login": "octocat"}}
    assert calls["count"] == 3


def test_run_graphql_query_raises_after_retryable_status_exhaustion(
    monkeypatch: MonkeyPatch,
) -> None:
    _patch_graphql_runtime(monkeypatch)
    monkeypatch.setattr(
        gql.requests,
        "post",
        lambda *_args, **_kwargs: _FakeResponse(status_code=504, text="Gateway Timeout"),
    )

    with pytest.raises(gql.GitHubGraphQLError, match="retryable status 504"):
        gql._run_graphql_query("query Ping { viewer { login } }", {})


def test_run_graphql_query_returns_partial_data_with_errors(monkeypatch: MonkeyPatch) -> None:
    _patch_graphql_runtime(monkeypatch)
    monkeypatch.setattr(
        gql.requests,
        "post",
        lambda *_args, **_kwargs: _FakeResponse(
            status_code=200,
            payload={
                "data": {"repository": {"name": "streamlit"}},
                "errors": [{"type": "NOT_FOUND", "message": "Could not resolve user"}],
            },
        ),
    )

    data = gql._run_graphql_query("query Repo { repository { name } }", {})

    assert data == {"repository": {"name": "streamlit"}}


def test_run_graphql_query_retries_internal_graphql_errors(monkeypatch: MonkeyPatch) -> None:
    _patch_graphql_runtime(monkeypatch)
    calls = {"count": 0}

    def fake_post(*_args: Any, **_kwargs: Any) -> _FakeResponse:
        calls["count"] += 1
        if calls["count"] == 1:
            return _FakeResponse(
                status_code=200,
                payload={
                    "data": None,
                    "errors": [{"type": "INTERNAL", "message": "Something went wrong while executing your query."}],
                },
            )
        return _FakeResponse(status_code=200, payload={"data": {"ok": True}})

    monkeypatch.setattr(gql.requests, "post", fake_post)

    data = gql._run_graphql_query("query Ping { viewer { login } }", {})

    assert data == {"ok": True}
    assert calls["count"] == 2


def test_run_graphql_query_retries_missing_data_payload(monkeypatch: MonkeyPatch) -> None:
    _patch_graphql_runtime(monkeypatch)
    calls = {"count": 0}

    def fake_post(*_args: Any, **_kwargs: Any) -> _FakeResponse:
        calls["count"] += 1
        if calls["count"] == 1:
            return _FakeResponse(status_code=200, payload={})
        return _FakeResponse(status_code=200, payload={"data": {"ok": True}})

    monkeypatch.setattr(gql.requests, "post", fake_post)

    data = gql._run_graphql_query("query Ping { viewer { login } }", {})

    assert data == {"ok": True}
    assert calls["count"] == 2


def test_fetch_merged_pr_metrics_keeps_partial_pages_on_later_failure(
    monkeypatch: MonkeyPatch,
) -> None:
    gql.fetch_merged_pr_metrics.clear()
    calls = {"count": 0}

    def fake_graphql(_query: str, _variables: dict[str, Any], **_kwargs: Any) -> dict[str, Any]:
        calls["count"] += 1
        if calls["count"] > 1:
            message = "received retryable status 502"
            raise gql.GitHubGraphQLError(message)
        return {
            "repository": {
                "pullRequests": {
                    "pageInfo": {"hasNextPage": True, "endCursor": "cursor-2"},
                    "edges": [
                        {
                            "node": {
                                "number": 1,
                                "url": "https://github.com/streamlit/streamlit/pull/1",
                                "title": "First",
                                "isDraft": False,
                                "createdAt": "2026-01-01T00:00:00Z",
                                "mergedAt": "2026-01-02T00:00:00Z",
                                "updatedAt": "2026-01-02T00:00:00Z",
                                "mergedBy": {"login": "lukasmasuch"},
                                "additions": 1,
                                "deletions": 0,
                                "changedFiles": 1,
                                "author": {"__typename": "User", "login": "lukasmasuch"},
                                "comments": {"totalCount": 0},
                                "reviews": {"nodes": []},
                                "closingIssuesReferences": {"nodes": []},
                                "labels": {"nodes": []},
                            }
                        }
                    ],
                }
            }
        }

    monkeypatch.setattr(gql, "_run_graphql_query", fake_graphql)

    df = gql.fetch_merged_pr_metrics(max_results=10)

    assert isinstance(df, pd.DataFrame)
    assert list(df["pr_number"]) == [1]
    assert calls["count"] == 2
