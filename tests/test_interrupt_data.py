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
    assert set(data["p0_p1_bugs"]["Title"]) == {"P0 confirmed bug"}
    assert set(data["confirmed_bugs_without_repro"]["Title"]) == {"Confirmed missing priority"}

    assert set(data["missing_labels_prs"]["Title"]) == {"Needs labels"}
    assert set(data["prs_needing_approval"]["Title"]) == {"Needs approval"}
    assert set(data["community_prs_ready_for_review"]["Title"]) == {"Needs approval", "Ready for review"}
    assert set(data["open_dependabot_prs"]["Title"]) == {"Dependabot update"}


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
            )
        ],
        "streamlit/streamlit-pdf": [
            _pr(
                number=103,
                repo="streamlit/streamlit-pdf",
                title="Pdf fix",
                labels=[],
                author="carol",
                updated_at="2026-02-12T10:00:00+00:00",
            )
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
        "streamlit/site": [
            _pr(
                number=105,
                repo="streamlit/site",
                title="Docs refresh",
                labels=[],
                author="erin",
                updated_at="2026-02-08T10:00:00+00:00",
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

    assert calls == [(repo, "open", 3) for repo in interrupt_data.MONITORED_INTERRUPT_REPOS]
    assert list(monitored_prs["Title"]) == [
        "Issues cleanup",
        "Pdf fix",
        "Gallery draft",
        "Bokeh cleanup",
        "Docs refresh",
    ]
    assert list(monitored_prs["Repository"]) == [
        "streamlit/st-issues",
        "streamlit/streamlit-pdf",
        "streamlit/gallery",
        "streamlit/streamlit-bokeh",
        "streamlit/site",
    ]
    assert list(monitored_prs["Draft"]) == [False, False, True, False, False]
