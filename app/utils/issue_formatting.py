from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

# Age offset so very new issues don't explode; sqrt decay is a mild HN-style gravity.
_IMPORTANCE_AGE_OFFSET_DAYS = 14.0
_SECONDS_PER_DAY = 86400.0

REACTION_EMOJI: dict[str, str] = {
    "+1": "👍",
    "-1": "👎",
    "confused": "😕",
    "eyes": "👀",
    "heart": "❤️",
    "hooray": "🎉",
    "laugh": "😄",
    "rocket": "🚀",
}


def reactions_to_str(reactions: Mapping[str, int]) -> str:
    """Format GitHub reactions into a compact emoji string."""
    return " ".join(
        f"{reactions.get(name, 0)} {emoji}" for name, emoji in REACTION_EMOJI.items() if reactions.get(name, 0) > 0
    )


def labels_to_type_emoji(label_names: Sequence[str]) -> str:
    """Map type labels to an emoji used in issue tables."""
    if "type:enhancement" in label_names:
        return "✨"
    if "type:bug" in label_names:
        return "🚨"
    if "type:docs" in label_names:
        return "📚"
    if "type:kudos" in label_names:
        return "🙏"
    return "❓"


def compute_importance_scores(
    created_at: pd.Series,
    engagement: pd.Series,
    views: pd.Series,
    *,
    now: datetime | None = None,
) -> pd.Series:
    """Age-weighted importance from existing issue totals.

    Uses creation date plus reaction+comment counts and view counts already on
    the issue. Views are log-scaled so the long tail (max ~5.7k vs median ~122)
    does not dominate. No per-event timestamps or extra API calls.
    """
    if now is None:
        now = datetime.now(UTC)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=UTC)

    now_ts = pd.Timestamp(now).tz_convert("UTC")
    created = pd.to_datetime(created_at, utc=True, errors="coerce")
    age_days = ((now_ts - created).dt.total_seconds() / _SECONDS_PER_DAY).clip(lower=0).fillna(0)

    engagement_n = pd.to_numeric(engagement, errors="coerce").reindex(created.index).fillna(0).clip(lower=0)
    views_n = pd.to_numeric(views, errors="coerce").reindex(created.index).fillna(0).clip(lower=0)

    combined = engagement_n.to_numpy(dtype="float64") + np.log1p(views_n.to_numpy(dtype="float64"))
    scores = combined / np.sqrt(age_days.to_numpy(dtype="float64") + _IMPORTANCE_AGE_OFFSET_DAYS)
    return pd.Series(scores, index=created.index, dtype="float64")


def get_issue_type(labels: Sequence[dict[str, Any]]) -> str | list[str]:
    """Return issue type labels used by reaction/stat pages."""
    is_bug = any(label.get("name") == "type:bug" for label in labels)
    is_enhancement = any(label.get("name") == "type:enhancement" for label in labels)

    if is_bug and is_enhancement:
        return ["Bug", "Enhancement"]
    if is_bug:
        return "Bug"
    if is_enhancement:
        return "Enhancement"
    return []
