from datetime import UTC, datetime, timedelta

import pandas as pd

from app.utils.issue_formatting import (
    compute_importance_scores,
    get_issue_type,
    labels_to_type_emoji,
    reactions_to_str,
)


def test_reactions_to_str_formats_only_non_zero_reactions() -> None:
    reactions = {
        "+1": 3,
        "-1": 0,
        "confused": 1,
        "eyes": 0,
        "heart": 2,
        "hooray": 0,
        "laugh": 0,
        "rocket": 0,
    }
    assert reactions_to_str(reactions) == "3 👍 1 😕 2 ❤️"


def test_labels_to_type_emoji_prefers_enhancement_then_bug() -> None:
    assert labels_to_type_emoji(["type:enhancement", "type:bug"]) == "✨"
    assert labels_to_type_emoji(["type:bug"]) == "🚨"
    assert labels_to_type_emoji(["other"]) == "❓"


def test_get_issue_type_returns_combined_types() -> None:
    labels = [{"name": "type:bug"}, {"name": "type:enhancement"}]
    assert get_issue_type(labels) == ["Bug", "Enhancement"]


def test_importance_scores_prefer_newer_and_more_engagement() -> None:
    now = datetime(2026, 9, 4, tzinfo=UTC)
    created_at = pd.Series(
        [
            now - timedelta(days=14),
            now - timedelta(days=365 * 3),
            now - timedelta(days=14),
            now - timedelta(days=14),
        ]
    )
    scores = compute_importance_scores(
        created_at,
        engagement=pd.Series([20, 20, 80, 0]),
        views=pd.Series([100, 100, 100, 0]),
        now=now,
    )

    newer, older, high_engagement, empty = scores.tolist()
    assert newer > older
    assert high_engagement > newer
    assert empty == 0


def test_importance_scores_views_boost_without_dominating() -> None:
    now = datetime(2026, 9, 4, tzinfo=UTC)
    created_at = pd.Series([now - timedelta(days=90), now - timedelta(days=90)])
    scores = compute_importance_scores(
        created_at,
        engagement=pd.Series([5, 80]),
        views=pd.Series([1500, 80]),
        now=now,
    )

    view_heavy, reaction_heavy = scores.tolist()
    assert reaction_heavy > view_heavy
    assert view_heavy > 0


def test_importance_scores_treat_missing_counts_as_zero() -> None:
    now = datetime(2026, 9, 4, tzinfo=UTC)
    created = now - timedelta(days=30)
    scores = compute_importance_scores(
        pd.Series([created, created]),
        engagement=pd.Series([10, None]),
        views=pd.Series([None, 50]),
        now=now,
    )

    assert scores.notna().all()
    assert scores.iloc[0] > 0
    assert scores.iloc[1] > 0
