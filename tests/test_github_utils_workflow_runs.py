from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

import pytest

from app.utils import github_utils
from app.utils.github_graphql_utils import GitHubGraphQLError

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def _graphql_run(
    *,
    run_id: int,
    created_at: str,
    sha: str,
    event: str = "push",
    branch: str | None = "develop",
    status: str = "COMPLETED",
    conclusion: str | None = "SUCCESS",
) -> dict[str, Any]:
    return {
        "databaseId": run_id,
        "createdAt": created_at,
        "event": event,
        "url": f"https://github.com/streamlit/streamlit/actions/runs/{run_id}",
        "checkSuite": {
            "databaseId": run_id + 1000,
            "status": status,
            "conclusion": conclusion,
            "branch": {"name": branch} if branch is not None else None,
            "commit": {"oid": sha},
        },
    }


def _graphql_page(nodes: list[dict[str, Any]], *, has_next: bool = False, cursor: str | None = None) -> dict[str, Any]:
    return {
        "node": {
            "runs": {
                "nodes": nodes,
                "pageInfo": {"endCursor": cursor, "hasNextPage": has_next},
            }
        }
    }


def test_fetch_workflow_runs_maps_graphql_to_rest_shape(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_workflow_runs.clear()
    monkeypatch.setattr(github_utils, "_get_workflow_node_id", lambda _name: "W_workflow")
    monkeypatch.setattr(
        github_utils,
        "_run_graphql_query",
        lambda _query, _variables: _graphql_page(
            [
                _graphql_run(
                    run_id=33074621326,
                    created_at="2026-08-27T13:00:29Z",
                    sha="ec763f7aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                )
            ]
        ),
    )

    runs = github_utils.fetch_workflow_runs("pr-preview.yml", limit=1)

    assert len(runs) == 1
    run = runs[0]
    assert run["id"] == 33074621326
    assert run["head_sha"] == "ec763f7aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert run["created_at"] == "2026-08-27T13:00:29Z"
    assert run["html_url"] == "https://github.com/streamlit/streamlit/actions/runs/33074621326"
    assert run["check_suite_id"] == 33074622326
    assert run["status"] == "completed"
    assert run["conclusion"] == "success"
    assert run["head_branch"] == "develop"
    assert run["event"] == "push"
    datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ")


def test_fetch_workflow_runs_filters_branch_and_success_locally(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_workflow_runs.clear()
    monkeypatch.setattr(github_utils, "_get_workflow_node_id", lambda _name: "W_workflow")
    monkeypatch.setattr(
        github_utils,
        "_run_graphql_query",
        lambda _query, _variables: _graphql_page(
            [
                _graphql_run(
                    run_id=1,
                    created_at="2026-08-27T13:00:29Z",
                    sha="aaa1111aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                    event="pull_request",
                    branch="feature/pr",
                ),
                _graphql_run(
                    run_id=2,
                    created_at="2026-08-27T12:00:00Z",
                    sha="bbb2222aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                    conclusion=None,
                    status="IN_PROGRESS",
                ),
                _graphql_run(
                    run_id=3,
                    created_at="2026-08-27T11:00:00Z",
                    sha="ccc3333aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                ),
            ]
        ),
    )

    runs = github_utils.fetch_workflow_runs("pr-preview.yml", limit=10)

    assert [run["id"] for run in runs] == [3]


def test_fetch_workflow_runs_paginates_until_limit(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_workflow_runs.clear()
    monkeypatch.setattr(github_utils, "_get_workflow_node_id", lambda _name: "W_workflow")
    calls: list[str | None] = []

    def fake_graphql(_query: str, variables: dict[str, Any]) -> dict[str, Any]:
        calls.append(variables["cursor"])
        if variables["cursor"] is None:
            return _graphql_page(
                [
                    _graphql_run(
                        run_id=1,
                        created_at="2026-08-27T13:00:00Z",
                        sha="aaa1111aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                        event="pull_request",
                        branch="feature/pr",
                    ),
                    _graphql_run(
                        run_id=2,
                        created_at="2026-08-27T12:00:00Z",
                        sha="bbb2222aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                    ),
                ],
                has_next=True,
                cursor="cursor-2",
            )
        return _graphql_page(
            [
                _graphql_run(
                    run_id=3,
                    created_at="2026-08-27T11:00:00Z",
                    sha="ccc3333aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                ),
                _graphql_run(
                    run_id=4,
                    created_at="2026-08-27T10:00:00Z",
                    sha="ddd4444aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                ),
            ]
        )

    monkeypatch.setattr(github_utils, "_run_graphql_query", fake_graphql)

    runs = github_utils.fetch_workflow_runs("playwright.yml", limit=2)

    assert [run["id"] for run in runs] == [2, 3]
    assert calls == [None, "cursor-2"]


def test_fetch_workflow_runs_stops_at_since_bound(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_workflow_runs.clear()
    monkeypatch.setattr(github_utils, "_get_workflow_node_id", lambda _name: "W_workflow")
    calls = {"count": 0}

    def fake_graphql(_query: str, _variables: dict[str, Any]) -> dict[str, Any]:
        calls["count"] += 1
        return _graphql_page(
            [
                _graphql_run(
                    run_id=1,
                    created_at="2026-08-20T12:00:00Z",
                    sha="aaa1111aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                ),
                _graphql_run(
                    run_id=2,
                    created_at="2026-08-01T12:00:00Z",
                    sha="bbb2222aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                ),
            ],
            has_next=True,
            cursor="should-not-be-used",
        )

    monkeypatch.setattr(github_utils, "_run_graphql_query", fake_graphql)

    runs = github_utils.fetch_workflow_runs("pr-preview.yml", limit=50, since=date(2026, 8, 10))

    assert [run["id"] for run in runs] == [1]
    assert calls["count"] == 1


def test_fetch_workflow_runs_without_branch_keeps_other_heads(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_workflow_runs.clear()
    monkeypatch.setattr(github_utils, "_get_workflow_node_id", lambda _name: "W_workflow")
    monkeypatch.setattr(
        github_utils,
        "_run_graphql_query",
        lambda _query, _variables: _graphql_page(
            [
                _graphql_run(
                    run_id=1,
                    created_at="2026-08-27T13:00:00Z",
                    sha="aaa1111aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                    event="pull_request",
                    branch="feature/pr",
                ),
                _graphql_run(
                    run_id=2,
                    created_at="2026-08-27T12:00:00Z",
                    sha="bbb2222aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                ),
            ]
        ),
    )

    runs = github_utils.fetch_workflow_runs("playwright.yml", limit=10, branch=None, status="success")

    assert [run["id"] for run in runs] == [1, 2]


def test_fetch_commit_shas_returns_newest_first(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_commit_shas.clear()
    captured: dict[str, object] = {}

    def fake_request_json(url: str, *, params: dict[str, object] | None = None, **_kwargs):
        captured["url"] = url
        captured["params"] = params
        return (
            [{"sha": "aaa1111aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}, {"sha": "bbb2222"}, {"not": "a-commit"}],
            None,
            200,
        )

    monkeypatch.setattr(github_utils, "_request_json", fake_request_json)

    shas = github_utils.fetch_commit_shas(branch="develop", limit=10)

    assert shas == ["aaa1111aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "bbb2222"]
    assert captured["url"] == "https://api.github.com/repos/streamlit/streamlit/commits"
    assert captured["params"] == {"sha": "develop", "per_page": 10}


def _check_run_node(*, name: str, status: str = "COMPLETED", conclusion: str | None = "SUCCESS") -> dict[str, Any]:
    return {
        "__typename": "CheckRun",
        "name": name,
        "status": status,
        "conclusion": conclusion,
    }


def _status_context_node(*, context: str, state: str = "SUCCESS") -> dict[str, Any]:
    return {"__typename": "StatusContext", "context": context, "state": state}


def _contexts_connection(
    nodes: list[dict[str, Any]],
    *,
    has_next: bool = False,
    cursor: str | None = None,
) -> dict[str, Any]:
    return {
        "pageInfo": {"hasNextPage": has_next, "endCursor": cursor},
        "nodes": nodes,
    }


def test_fetch_develop_commit_checks_maps_check_runs_and_statuses(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_develop_commit_checks.clear()
    monkeypatch.setattr(
        github_utils,
        "_run_graphql_query",
        lambda _query, _variables: {
            "repository": {
                "ref": {
                    "target": {
                        "history": {
                            "nodes": [
                                {
                                    "oid": "aaa1111aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                                    "statusCheckRollup": {
                                        "contexts": _contexts_connection(
                                            [
                                                _check_run_node(name="Python tests"),
                                                _status_context_node(context="codecov/patch", state="FAILURE"),
                                            ]
                                        )
                                    },
                                }
                            ]
                        }
                    }
                }
            }
        },
    )

    commits = github_utils.fetch_develop_commit_checks(limit=10)

    assert len(commits) == 1
    assert commits[0]["sha"] == "aaa1111aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert commits[0]["checks"] == [
        {
            "name": "Python tests",
            "kind": "check_run",
            "status": "completed",
            "conclusion": "success",
            "state": None,
        },
        {
            "name": "codecov/patch",
            "kind": "status",
            "status": None,
            "conclusion": None,
            "state": "failure",
        },
    ]


def test_fetch_develop_commit_checks_paginates_contexts(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_develop_commit_checks.clear()
    calls: list[str | None] = []

    def fake_graphql(_query: str, variables: dict[str, Any]) -> dict[str, Any]:
        calls.append(variables.get("cursor"))
        if "historyFirst" in variables:
            return {
                "repository": {
                    "ref": {
                        "target": {
                            "history": {
                                "nodes": [
                                    {
                                        "oid": "aaa1111aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                                        "statusCheckRollup": {
                                            "contexts": _contexts_connection(
                                                [_check_run_node(name="page-1")],
                                                has_next=True,
                                                cursor="cursor-2",
                                            )
                                        },
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        return {
            "repository": {
                "object": {"statusCheckRollup": {"contexts": _contexts_connection([_check_run_node(name="page-2")])}}
            }
        }

    monkeypatch.setattr(github_utils, "_run_graphql_query", fake_graphql)

    commits = github_utils.fetch_develop_commit_checks(limit=10)

    assert [check["name"] for check in commits[0]["checks"]] == ["page-1", "page-2"]
    assert calls == [None, "cursor-2"]


def _fail_if_st_error(*_args: Any, **_kwargs: Any) -> None:
    message = "st.error should not be used from GraphQL cache helpers"
    raise AssertionError(message)


def test_fetch_workflow_runs_does_not_use_st_error_on_total_failure(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_workflow_runs.clear()
    monkeypatch.setattr(github_utils, "_get_workflow_node_id", lambda _name: "W_workflow")
    monkeypatch.setattr(github_utils.st, "error", _fail_if_st_error)

    def fake_graphql(_query: str, _variables: dict[str, Any]) -> dict[str, Any]:
        message = "received retryable status 502"
        raise GitHubGraphQLError(message)

    monkeypatch.setattr(github_utils, "_run_graphql_query", fake_graphql)

    with pytest.raises(GitHubGraphQLError, match="retryable status 502"):
        github_utils.fetch_workflow_runs("playwright.yml", limit=1)


def test_fetch_workflow_runs_keeps_partial_results_on_later_page_failure(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_workflow_runs.clear()
    monkeypatch.setattr(github_utils, "_get_workflow_node_id", lambda _name: "W_workflow")
    monkeypatch.setattr(github_utils.st, "error", _fail_if_st_error)
    calls = {"count": 0}

    def fake_graphql(_query: str, _variables: dict[str, Any]) -> dict[str, Any]:
        calls["count"] += 1
        if calls["count"] == 1:
            return _graphql_page(
                [
                    _graphql_run(
                        run_id=11,
                        created_at="2026-08-27T13:00:00Z",
                        sha="aaa1111aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                    )
                ],
                has_next=True,
                cursor="cursor-2",
            )
        message = "received retryable status 504"
        raise GitHubGraphQLError(message)

    monkeypatch.setattr(github_utils, "_run_graphql_query", fake_graphql)

    runs = github_utils.fetch_workflow_runs("playwright.yml", limit=50)

    assert [run["id"] for run in runs] == [11]
    assert calls["count"] == 2


def test_fetch_develop_commit_checks_does_not_use_st_error_on_failure(monkeypatch: MonkeyPatch) -> None:
    github_utils.fetch_develop_commit_checks.clear()
    monkeypatch.setattr(github_utils.st, "error", _fail_if_st_error)

    def fake_graphql(_query: str, _variables: dict[str, Any]) -> dict[str, Any]:
        message = "ChunkedEncodingError: Response ended prematurely"
        raise GitHubGraphQLError(message)

    monkeypatch.setattr(github_utils, "_run_graphql_query", fake_graphql)

    with pytest.raises(GitHubGraphQLError, match="ChunkedEncodingError"):
        github_utils.fetch_develop_commit_checks(limit=10)


def test_fetch_remaining_check_contexts_keeps_partial_on_later_failure(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(github_utils.st, "error", _fail_if_st_error)
    calls = {"count": 0}

    def fake_graphql(_query: str, _variables: dict[str, Any]) -> dict[str, Any]:
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "repository": {
                    "object": {
                        "statusCheckRollup": {
                            "contexts": _contexts_connection(
                                [_check_run_node(name="page-2")],
                                has_next=True,
                                cursor="cursor-3",
                            )
                        }
                    }
                }
            }
        message = "received retryable status 502"
        raise GitHubGraphQLError(message)

    monkeypatch.setattr(github_utils, "_run_graphql_query", fake_graphql)

    checks = github_utils._fetch_remaining_check_contexts("aaa1111aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "cursor-2")

    assert [check["name"] for check in checks] == ["page-2"]
    assert calls["count"] == 2
