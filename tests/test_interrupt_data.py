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

    monkeypatch.setattr(interrupt_data, "get_interrupt_data_snapshot", lambda: (issues, prs))
    monkeypatch.setattr(interrupt_data, "get_reproducible_example_exists", lambda issue_number: issue_number == 3)
    interrupt_data.build_interrupt_action_items.clear()

    data = interrupt_data.build_interrupt_action_items(date(2026, 2, 1))

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


def test_build_interrupt_action_items_clear_busts_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = {"value": 0}

    def fake_snapshot() -> tuple[list[dict], list[dict]]:
        call_count["value"] += 1
        return [], []

    monkeypatch.setattr(interrupt_data, "get_interrupt_data_snapshot", fake_snapshot)
    interrupt_data.build_interrupt_action_items.clear()

    since = date(2026, 2, 1)
    interrupt_data.build_interrupt_action_items(since)
    interrupt_data.build_interrupt_action_items(since)
    assert call_count["value"] == 1

    interrupt_data.build_interrupt_action_items.clear()
    interrupt_data.build_interrupt_action_items(since)
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
    calls: list[tuple[str, str]] = []

    def fake_get_all_github_prs(
        state: str = "all",
        repo: str = "streamlit/streamlit",
    ) -> list[dict]:
        calls.append((repo, state))
        return repo_payloads[repo]

    monkeypatch.setattr(interrupt_data, "get_all_github_prs", fake_get_all_github_prs)
    interrupt_data.get_monitored_repo_open_prs.clear()

    monitored_prs = interrupt_data.get_monitored_repo_open_prs()

    expected_bot_only_repos = [
        repo for repo in interrupt_data.BOT_PR_INTERRUPT_REPOS if repo not in interrupt_data.MONITORED_INTERRUPT_REPOS
    ]
    assert calls == [(repo, "open") for repo in interrupt_data.MONITORED_INTERRUPT_REPOS] + [
        (repo, "open") for repo in expected_bot_only_repos
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


def _check_run(
    *,
    name: str,
    status: str = "completed",
    conclusion: str | None = "success",
) -> dict:
    return {
        "name": name,
        "kind": "check_run",
        "status": status,
        "conclusion": conclusion,
        "state": None,
    }


def _status_context(*, name: str, state: str = "success") -> dict:
    return {
        "name": name,
        "kind": "status",
        "status": None,
        "conclusion": None,
        "state": state,
    }


def test_check_failed_ignores_ineligible_conclusions() -> None:
    assert interrupt_data._check_failed(_check_run(name="lint", conclusion="failure")) is True
    assert interrupt_data._check_failed(_check_run(name="lint", conclusion="timed_out")) is True
    assert interrupt_data._check_failed(_check_run(name="lint", conclusion="success")) is False
    assert interrupt_data._check_failed(_check_run(name="lint", conclusion="skipped")) is None
    assert interrupt_data._check_failed(_check_run(name="lint", status="in_progress", conclusion=None)) is None
    assert interrupt_data._check_failed(_status_context(name="codecov", state="failure")) is True
    assert interrupt_data._check_failed(_status_context(name="codecov", state="error")) is True
    assert interrupt_data._check_failed(_status_context(name="codecov", state="success")) is False
    assert interrupt_data._check_failed(_status_context(name="codecov", state="pending")) is None


def test_compute_ci_failed_check_metrics_uses_all_checks() -> None:
    commits = [
        {
            "sha": "sha-new",
            "checks": [
                _check_run(name="python", conclusion="success"),
                _check_run(name="playwright", conclusion="failure"),
                _check_run(name="preview", conclusion="skipped"),
                _status_context(name="codecov", state="success"),
            ],
        },
        {
            "sha": "sha-old",
            "checks": [
                _check_run(name="python", conclusion="success"),
                _check_run(name="js", conclusion="success"),
                _check_run(name="lint", status="in_progress", conclusion=None),
            ],
        },
    ]

    percent, failing, total = interrupt_data._compute_ci_failed_check_metrics(commits)

    # Eligible: old python+js success, new python+playwright+codecov with 1 failure.
    assert (percent, failing, total) == (100.0 * 1 / 5, 1, 5)


def test_get_ci_failing_test_run_metrics_uses_develop_commit_checks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_fetch_develop_commit_checks(limit: int = 10) -> list[dict]:
        assert limit == interrupt_data.DEVELOP_COMMIT_WINDOW
        return [
            {
                "sha": "sha-new",
                "checks": [
                    _check_run(name="python", conclusion="success"),
                    _check_run(name="playwright", conclusion="failure"),
                ],
            },
            {
                "sha": "sha-old",
                "checks": [
                    _check_run(name="python", conclusion="success"),
                    _check_run(name="js", conclusion="success"),
                ],
            },
        ]

    monkeypatch.setattr(interrupt_data, "fetch_develop_commit_checks", fake_fetch_develop_commit_checks)
    interrupt_data.get_ci_failing_test_run_metrics.clear()

    percent, failing, total = interrupt_data.get_ci_failing_test_run_metrics()

    assert (percent, failing, total) == (25.0, 1, 4)


def _annotation(
    *,
    level: str,
    path: str,
    start_line: int,
    message: str,
) -> dict:
    return {
        "annotation_level": level,
        "path": path,
        "start_line": start_line,
        "message": message,
    }


def test_unique_annotation_rows_dedupes_and_normalizes() -> None:
    rows = interrupt_data._unique_annotation_rows(
        [
            _annotation(
                level="warning",
                path="uvloop/__init__.py",
                start_line=160,
                message="'asyncio.set_event_loop_policy' is deprecated",
            ),
            _annotation(
                level="warning",
                path="uvloop/__init__.py",
                start_line=160,
                message="'asyncio.set_event_loop_policy' is deprecated",
            ),
            _annotation(
                level="failure",
                path=".github",
                start_line=551,
                message="Event loop is closed",
            ),
            _annotation(
                level="warning",
                path="_pytest/raises.py",
                start_line=697,
                message="unclosed database in <sqlite3.Connection object at 0x7fa832f3a5c0>",
            ),
            _annotation(
                level="warning",
                path="_pytest/raises.py",
                start_line=697,
                message="unclosed database in <sqlite3.Connection object at 0xabc123>",
            ),
            _annotation(
                level="warning",
                path="_pytest/threadexception.py",
                start_line=58,
                message="Exception in thread ScriptRunner.scriptThread\n\nTraceback...",
            ),
        ],
        job_name="py-unit-tests (max)",
        job_url="https://example.test/job/py",
    )

    by_message = {row["Message"]: row for row in rows}
    assert by_message["'asyncio.set_event_loop_policy' is deprecated"]["Count"] == 2
    assert by_message["Event loop is closed"]["Level"] == "error"
    assert by_message["Event loop is closed"]["Location"] == ".github#L551"
    assert by_message["unclosed database in <sqlite3.Connection object at 0x7fa832f3a5c0>"]["Count"] == 2
    assert by_message["Exception in thread ScriptRunner.scriptThread"]["Count"] == 1
    assert {row["URL"] for row in rows} == {"https://example.test/job/py"}
    assert len(rows) == 4


def test_get_ci_test_annotations_combines_python_and_js_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_fetch_workflow_runs(
        workflow_name: str,
        limit: int = 50,
        since=None,
        branch: str | None = "develop",
        status: str | None = "success",
    ) -> list[dict]:
        assert limit == 1
        assert branch == "develop"
        assert status == "success"
        run_id = 1 if workflow_name == interrupt_data.PYTHON_TESTS_WORKFLOW else 2
        return [
            {
                "id": run_id,
                "html_url": f"https://example.test/runs/{workflow_name}",
                "created_at": "2026-08-30T00:00:00Z",
            }
        ]

    def fake_jobs(run_id: int) -> list[dict]:
        if run_id == 1:
            return [
                {
                    "id": 11,
                    "name": interrupt_data.PYTHON_UNIT_TESTS_MAX_JOB,
                    "html_url": "https://example.test/job/py",
                }
            ]
        return [
            {
                "id": 22,
                "name": interrupt_data.JS_UNIT_TESTS_JOB,
                "html_url": "https://example.test/job/js",
            }
        ]

    def fake_annotations(check_run_id: int) -> list[dict]:
        if check_run_id == 11:
            return [
                _annotation(
                    level="warning",
                    path="uvloop/__init__.py",
                    start_line=160,
                    message="'asyncio.set_event_loop_policy' is deprecated",
                ),
                _annotation(
                    level="warning",
                    path="uvloop/__init__.py",
                    start_line=160,
                    message="'asyncio.set_event_loop_policy' is deprecated",
                ),
            ]
        return [
            _annotation(
                level="notice",
                path="knip.json",
                start_line=1,
                message="Remove from ignoreDependencies: react-responsive-carousel in knip.json",
            )
        ]

    monkeypatch.setattr(interrupt_data, "fetch_workflow_runs", fake_fetch_workflow_runs)
    monkeypatch.setattr(interrupt_data, "fetch_workflow_run_jobs", fake_jobs)
    monkeypatch.setattr(interrupt_data, "fetch_workflow_run_annotations", fake_annotations)
    interrupt_data.get_ci_test_annotations.clear()

    annotations_df, sources = interrupt_data.get_ci_test_annotations()

    assert list(annotations_df["Job"]) == [
        interrupt_data.PYTHON_UNIT_TESTS_MAX_JOB,
        interrupt_data.JS_UNIT_TESTS_JOB,
    ]
    assert list(annotations_df["Level"]) == ["warning", "notice"]
    assert list(annotations_df["Count"]) == [2, 1]
    assert list(annotations_df["Location"]) == ["uvloop/__init__.py#L160", "knip.json#L1"]
    assert [source["job_url"] for source in sources] == [
        "https://example.test/job/py",
        "https://example.test/job/js",
    ]


def test_get_ci_test_annotations_missing_job_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_fetch_workflow_runs(workflow_name: str, **_: object) -> list[dict]:
        return [{"id": 1, "html_url": "https://example.test/run", "created_at": "2026-08-30T00:00:00Z"}]

    monkeypatch.setattr(interrupt_data, "fetch_workflow_runs", fake_fetch_workflow_runs)
    monkeypatch.setattr(interrupt_data, "fetch_workflow_run_jobs", lambda _run_id: [])
    monkeypatch.setattr(interrupt_data, "fetch_workflow_run_annotations", lambda _check_run_id: [])
    interrupt_data.get_ci_test_annotations.clear()

    annotations_df, sources = interrupt_data.get_ci_test_annotations()

    assert annotations_df.empty
    assert [source["job_url"] for source in sources] == ["", ""]
    assert [source["job"] for source in sources] == [
        interrupt_data.PYTHON_UNIT_TESTS_MAX_JOB,
        interrupt_data.JS_UNIT_TESTS_JOB,
    ]


def test_clear_interrupt_caches_clears_page_and_nested_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    cleared: list[str] = []

    def fake_clear(name: str):
        def _clear() -> None:
            cleared.append(name)

        return _clear

    targets = [
        "get_ci_test_annotations",
        "get_flaky_tests",
        "build_interrupt_action_items",
        "fetch_workflow_runs",
        "fetch_workflow_run_jobs",
        "fetch_workflow_run_annotations",
        "get_all_github_issues",
        "get_all_github_prs",
        "fetch_develop_commit_checks",
        "fetch_wiki_issue_repros",
        "get_synced_wiki_repo_path",
    ]
    for name in targets:
        monkeypatch.setattr(getattr(interrupt_data, name), "clear", fake_clear(name))

    interrupt_data.clear_interrupt_caches()

    assert set(targets) <= set(cleared)
