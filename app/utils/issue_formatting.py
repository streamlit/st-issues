from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

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
