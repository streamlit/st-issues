from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from app.utils import interrupt_data

if TYPE_CHECKING:
    import pytest


def _issue(
    *,
    number: int,
    title: str,
    labels: list[str],
    created_at: str = "2026-02-10T00:00:00+00:00",
    author: str = "issue-author",
    assignees: list[str] | None = None,
) -> dict:
    return {
        "number": number,
        "title": title,
        "html_url": f"https://github.com/streamlit/streamlit/issues/{number}",
        "created_at": created_at,
        "user": {"login": author},
        "labels": [{"name": label} for label in labels],
        "assignees": [{"login": assignee} for assignee in (assignees or [])],
    }


def _pr(
    *,
    number: int,
    title: str,
    labels: list[str],
    author: str,
    repo: str = "streamlit/streamlit",
    draft: bool = False,
    created_at: str = "2026-02-10T00:00:00+00:00",
    updated_at: str = "2026-02-11T00:00:00+00:00",
    assignees: list[str] | None = None,
) -> dict:
    return {
        "number": number,
        "title": title,
        "html_url": f"https://github.com/{repo}/pull/{number}",
        "created_at": created_at,
        "updated_at": updated_at,
        "draft": draft,
        "user": {"login": author},
        "labels": [{"name": label} for label in labels],
        "assignees": [{"login": assignee} for assignee in (assignees or [])],
    }


def test_build_interrupt_action_items_shapes(monkeypatch: pytest.MonkeyPatch) -> None:
    issues = [
        _issue(number=1, title="Needs triage issue", labels=["status:needs-triage", "type:bug"]),
        _issue(number=2, title="Confirmed missing priority", labels=["type:bug", "status:confirmed"]),
        _issue(
            number=3,
            title="P0 confirmed bug",
            labels=["type:bug", "status:confirmed", "priority:P0"],
            assignees=["alice"],
        ),
        _issue(number=4, title="Waiting for team", labels=["status:awaiting-team-response", "feature:chat"]),
        _issue(number=5, title="Kudos issue", labels=["type:kudos"]),
        _issue(
            number=6,
            title="Multipage bug",
            labels=["type:bug", "status:confirmed", "feature:multipage-apps"],
        ),
        _issue(
            number=7,
            title="P2 confirmed bug",
            labels=["type:bug", "status:confirmed", "priority:P2", "feature:chat"],
            created_at="2026-01-15T00:00:00+00:00",
        ),
    ]
    prs = [
        _pr(number=10, title="Needs labels", labels=["impact:users"], author="community-author"),
        _pr(number=11, title="Needs approval", labels=["change:feature", "impact:users"], author="community-author"),
        _pr(
            number=12,
            title="Ready for review",
            labels=["change:enhancement", "impact:users"],
            author="community-author",
            assignees=["reviewer"],
        ),
        _pr(number=13, title="Dependabot update", labels=["dependencies"], author="dependabot[bot]"),
        _pr(
            number=14,
            title="Draft PR",
            labels=["change:enhancement", "impact:users"],
            author="community-author",
            draft=True,
        ),
        _pr(number=15, title="Internal PR", labels=["change:enhancement", "impact:users"], author="sfc-gh-bnisco"),
        _pr(number=16, title="[chore] Release v1.61.0", labels=["change:chore"], author="github-actions[bot]"),
        _pr(number=17, title="[snapshots] Update E2E snapshots for #15693", labels=[], author="github-actions[bot]"),
        _pr(number=18, title="[chore] Release v1.62.0", labels=[], author="sfc-gh-release-manager"),
        _pr(
            number=201,
            title="Docs github-actions PR",
            labels=[],
            author="github-actions[bot]",
            repo="streamlit/docs",
        ),
    ]

    monkeypatch.setattr(interrupt_data, "get_interrupt_data_snapshot", lambda refresh_nonce=0: (issues, prs))
    monkeypatch.setattr(interrupt_data, "get_reproducible_example_exists", lambda issue_number: issue_number == 3)
    interrupt_data.build_interrupt_action_items.clear()

    data = interrupt_data.build_interrupt_action_items(date(2026, 2, 1), refresh_nonce=7)

    assert set(data["needs_triage"]["Title"]) == {"Needs triage issue"}
    assert set(data["missing_labels_issues"]["Title"]) == {
        "Needs triage issue",
        "Confirmed missing priority",
        "P0 confirmed bug",
    }
    assert set(data["waiting_for_team_response"]["Title"]) == {"Waiting for team"}
    assert set(data["unprioritized_bugs"]["Title"]) == {"Confirmed missing priority", "Multipage bug"}
    assert set(data["high_priority_bugs"]["Title"]) == {"P0 confirmed bug", "P2 confirmed bug"}
    assert set(data["confirmed_bugs_without_repro"]["Title"]) == {"Confirmed missing priority"}

    assert set(data["missing_labels_prs"]["Title"]) == {"Needs labels"}
    assert set(data["prs_needing_approval"]["Title"]) == {"Needs approval"}
    assert set(data["community_prs_ready_for_review"]["Title"]) == {"Needs approval", "Ready for review"}
    # Only streamlit/streamlit bot PRs, excluding automated release PRs (those have their
    # own section). Docs bot PRs belong in the important-repos table instead.
    assert set(data["open_bot_prs"]["Title"]) == {
        "Dependabot update",
        "[snapshots] Update E2E snapshots for #15693",
    }
    # Only `github-actions[bot]` PRs with the release title prefix count: the snapshot-update bot
    # PR lands in open_bot_prs instead, and the human-authored release PR is excluded.
    assert set(data["open_release_prs"]["Title"]) == {"[chore] Release v1.61.0"}


def test_build_interrupt_action_items_refresh_nonce_busts_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = {"value": 0}

    def fake_snapshot(refresh_nonce: int = 0) -> tuple[list[dict], list[dict]]:
        call_count["value"] += 1
        return [], []

    monkeypatch.setattr(interrupt_data, "get_interrupt_data_snapshot", fake_snapshot)
    interrupt_data.build_interrupt_action_items.clear()

    since = date(2026, 2, 1)
    interrupt_data.build_interrupt_action_items(since, refresh_nonce=0)
    interrupt_data.build_interrupt_action_items(since, refresh_nonce=0)
    assert call_count["value"] == 1

    interrupt_data.build_interrupt_action_items(since, refresh_nonce=1)
    assert call_count["value"] == 2


def test_get_monitored_repo_open_prs(monkeypatch: pytest.MonkeyPatch) -> None:
    repo_payloads = {
        "streamlit/docs": [
            _pr(
                number=201,
                repo="streamlit/docs",
                title="Automated sitemap update",
                labels=[],
                author="github-actions[bot]",
                updated_at="2026-02-14T10:00:00+00:00",
            ),
            _pr(
                number=202,
                repo="streamlit/docs",
                title="Bump mkdocs in docs",
                labels=["dependencies"],
                author="dependabot[bot]",
                updated_at="2026-02-13T12:00:00+00:00",
            ),
            _pr(
                number=203,
                repo="streamlit/docs",
                title="Human docs PR",
                labels=[],
                author="docs-author",
                updated_at="2026-02-15T10:00:00+00:00",
            ),
        ],
        "streamlit/streamlit-pivot-table": [
            _pr(
                number=301,
                repo="streamlit/streamlit-pivot-table",
                title="Bump frontend deps in pivot-table",
                labels=["dependencies"],
                author="dependabot[bot]",
                updated_at="2026-02-16T10:00:00+00:00",
            ),
            _pr(
                number=302,
                repo="streamlit/streamlit-pivot-table",
                title="Human pivot-table PR",
                labels=[],
                author="pivot-author",
                updated_at="2026-02-17T10:00:00+00:00",
            ),
            _pr(
                number=303,
                repo="streamlit/streamlit-pivot-table",
                title="Pivot-table github-actions PR",
                labels=[],
                author="github-actions[bot]",
                updated_at="2026-02-15T10:00:00+00:00",
            ),
        ],
        "streamlit/blank-app-template": [
            _pr(
                number=401,
                repo="streamlit/blank-app-template",
                title="Bump uv in blank-app-template",
                labels=["dependencies"],
                author="dependabot[bot]",
                updated_at="2026-02-18T10:00:00+00:00",
            ),
            _pr(
                number=402,
                repo="streamlit/blank-app-template",
                title="Human blank-app PR",
                labels=[],
                author="template-author",
                updated_at="2026-02-19T10:00:00+00:00",
            ),
        ],
        "streamlit/gallery": [
            _pr(
                number=101,
                repo="streamlit/gallery",
                title="Gallery draft",
                labels=[],
                author="alice",
                draft=True,
                updated_at="2026-02-11T10:00:00+00:00",
            )
        ],
        "streamlit/component-template": [],
        "streamlit/streamlit-bokeh": [
            _pr(
                number=102,
                repo="streamlit/streamlit-bokeh",
                title="Bokeh cleanup",
                labels=[],
                author="bob",
                updated_at="2026-02-09T10:00:00+00:00",
            ),
            _pr(
                number=105,
                repo="streamlit/streamlit-bokeh",
                title="Bump bokeh in streamlit-bokeh",
                labels=["dependencies"],
                author="dependabot[bot]",
                updated_at="2026-02-10T12:00:00+00:00",
            ),
        ],
        "streamlit/streamlit-pdf": [
            _pr(
                number=103,
                repo="streamlit/streamlit-pdf",
                title="Pdf fix",
                labels=[],
                author="carol",
                updated_at="2026-02-12T10:00:00+00:00",
            ),
            _pr(
                number=106,
                repo="streamlit/streamlit-pdf",
                title="Bump pdf.js in streamlit-pdf",
                labels=["dependencies"],
                author="dependabot[bot]",
                updated_at="2026-02-12T12:00:00+00:00",
            ),
        ],
        "streamlit/agent-skills": [],
        "streamlit/st-issues": [
            _pr(
                number=104,
                repo="streamlit/st-issues",
                title="Issues cleanup",
                labels=[],
                author="dave",
                updated_at="2026-02-13T10:00:00+00:00",
            )
        ],
    }
    calls: list[tuple[str, str, int]] = []

    def fake_get_all_github_prs(
        state: str = "all",
        refresh_nonce: int = 0,
        repo: str = "streamlit/streamlit",
    ) -> list[dict]:
        calls.append((repo, state, refresh_nonce))
        return repo_payloads[repo]

    monkeypatch.setattr(interrupt_data, "get_all_github_prs", fake_get_all_github_prs)
    interrupt_data.get_monitored_repo_open_prs.clear()

    monitored_prs = interrupt_data.get_monitored_repo_open_prs(refresh_nonce=3)

    expected_bot_only_repos = [
        repo for repo in interrupt_data.BOT_PR_INTERRUPT_REPOS if repo not in interrupt_data.MONITORED_INTERRUPT_REPOS
    ]
    assert calls == [(repo, "open", 3) for repo in interrupt_data.MONITORED_INTERRUPT_REPOS] + [
        (repo, "open", 3) for repo in expected_bot_only_repos
    ]
    assert list(monitored_prs["Title"]) == [
        "Bump uv in blank-app-template",
        "Bump frontend deps in pivot-table",
        "Pivot-table github-actions PR",
        "Automated sitemap update",
        "Bump mkdocs in docs",
        "Issues cleanup",
        "Bump pdf.js in streamlit-pdf",
        "Pdf fix",
        "Gallery draft",
        "Bump bokeh in streamlit-bokeh",
        "Bokeh cleanup",
    ]
    assert list(monitored_prs["Repository"]) == [
        "streamlit/blank-app-template",
        "streamlit/streamlit-pivot-table",
        "streamlit/streamlit-pivot-table",
        "streamlit/docs",
        "streamlit/docs",
        "streamlit/st-issues",
        "streamlit/streamlit-pdf",
        "streamlit/streamlit-pdf",
        "streamlit/gallery",
        "streamlit/streamlit-bokeh",
        "streamlit/streamlit-bokeh",
    ]
    assert list(monitored_prs["Draft"]) == [
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        True,
        False,
        False,
    ]
    assert list(monitored_prs["Author"]) == [
        "dependabot[bot]",
        "dependabot[bot]",
        "github-actions[bot]",
        "github-actions[bot]",
        "dependabot[bot]",
        "dave",
        "dependabot[bot]",
        "carol",
        "alice",
        "dependabot[bot]",
        "bob",
    ]


def _workflow_run(
    *,
    run_id: int,
    sha: str,
    status: str = "completed",
    conclusion: str | None = "success",
) -> dict:
    return {
        "id": run_id,
        "head_sha": sha,
        "status": status,
        "conclusion": conclusion,
    }


def test_latest_completed_runs_for_commits_keeps_newest_eligible_run() -> None:
    commit_shas = ["sha-new", "sha-old"]
    runs = [
        _workflow_run(run_id=1, sha="sha-new", status="in_progress", conclusion=None),
        _workflow_run(run_id=2, sha="sha-new", conclusion="failure"),
        _workflow_run(run_id=3, sha="sha-new", conclusion="success"),
        _workflow_run(run_id=4, sha="sha-old", conclusion="cancelled"),
        _workflow_run(run_id=5, sha="sha-old", conclusion="success"),
        _workflow_run(run_id=6, sha="sha-other", conclusion="failure"),
    ]

    selected = interrupt_data._latest_completed_runs_for_commits(runs, commit_shas)

    assert [run["id"] for run in selected] == [2, 5]


def test_run_had_failing_test_uses_playwright_stats_and_conclusion() -> None:
    playwright_success = {**_workflow_run(run_id=1, sha="a"), "_workflow": "playwright.yml"}
    python_failure = {**_workflow_run(run_id=2, sha="a", conclusion="failure"), "_workflow": "python-tests.yml"}
    python_success = {**_workflow_run(run_id=3, sha="a"), "_workflow": "python-tests.yml"}

    assert interrupt_data._run_had_failing_test(
        playwright_success,
        playwright_stats={"summary": {"failed": 0, "errors": 0, "tests_with_reruns": 2}},
    )
    assert not interrupt_data._run_had_failing_test(
        playwright_success,
        playwright_stats={"summary": {"failed": 0, "errors": 0, "tests_with_reruns": 0}},
    )
    assert not interrupt_data._run_had_failing_test(playwright_success, playwright_stats=None)
    assert interrupt_data._run_had_failing_test(
        {**playwright_success, "conclusion": "failure"},
        playwright_stats=None,
    )
    assert interrupt_data._run_had_failing_test(python_failure)
    assert not interrupt_data._run_had_failing_test(python_success)


def test_compute_ci_failing_test_run_metrics_percentage_and_order() -> None:
    commit_shas = ["sha-new", "sha-old"]
    runs_by_workflow = {
        "python-tests.yml": [
            _workflow_run(run_id=11, sha="sha-new"),
            _workflow_run(run_id=12, sha="sha-old", conclusion="failure"),
        ],
        "js-tests.yml": [
            _workflow_run(run_id=21, sha="sha-new"),
            _workflow_run(run_id=22, sha="sha-old"),
        ],
        "playwright.yml": [
            _workflow_run(run_id=31, sha="sha-new"),
            _workflow_run(run_id=32, sha="sha-old"),
        ],
    }
    playwright_stats = {
        31: {"summary": {"failed": 0, "errors": 0, "tests_with_reruns": 1}},
        32: {"summary": {"failed": 0, "errors": 0, "tests_with_reruns": 0}},
    }

    percent, failing, total, flags = interrupt_data._compute_ci_failing_test_run_metrics(
        commit_shas,
        runs_by_workflow,
        playwright_stats,
    )

    # Oldest commit first: python failure, js success, playwright success,
    # then newest: python success, js success, playwright reruns.
    assert (percent, failing, total) == (100.0 * 2 / 6, 2, 6)
    assert flags == [1, 0, 0, 0, 0, 1]


def test_get_ci_failing_test_run_metrics_uses_develop_commit_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_fetch_commit_shas(branch: str = "develop", limit: int = 10, refresh_nonce: int = 0) -> list[str]:
        assert branch == "develop"
        assert limit == interrupt_data.DEVELOP_COMMIT_WINDOW
        assert refresh_nonce == 4
        return ["sha-new", "sha-old"]

    def fake_fetch_workflow_runs(
        workflow_name: str,
        limit: int = 50,
        since=None,
        branch: str | None = "develop",
        status: str | None = "success",
    ) -> list[dict]:
        assert branch == "develop"
        assert status is None
        if workflow_name == "python-tests.yml":
            return [
                _workflow_run(run_id=11, sha="sha-new"),
                _workflow_run(run_id=12, sha="sha-old", conclusion="failure"),
            ]
        if workflow_name == "js-tests.yml":
            return [
                _workflow_run(run_id=21, sha="sha-new"),
                _workflow_run(run_id=22, sha="sha-old"),
            ]
        return [
            _workflow_run(run_id=31, sha="sha-new"),
            _workflow_run(run_id=32, sha="sha-old"),
        ]

    def fake_load_playwright_test_stats(run_id: int) -> dict | None:
        if run_id == 31:
            return {"summary": {"failed": 0, "errors": 0, "tests_with_reruns": 1}}
        return {"summary": {"failed": 0, "errors": 0, "tests_with_reruns": 0}}

    monkeypatch.setattr(interrupt_data, "fetch_commit_shas", fake_fetch_commit_shas)
    monkeypatch.setattr(interrupt_data, "fetch_workflow_runs", fake_fetch_workflow_runs)
    monkeypatch.setattr(interrupt_data, "_load_playwright_test_stats", fake_load_playwright_test_stats)
    interrupt_data.get_ci_failing_test_run_metrics.clear()

    percent, failing, total, flags = interrupt_data.get_ci_failing_test_run_metrics(refresh_nonce=4)

    assert (percent, failing, total) == (100.0 * 2 / 6, 2, 6)
    assert flags == [1, 0, 0, 0, 0, 1]
