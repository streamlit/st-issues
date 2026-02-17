from app.utils.issue_formatting import get_issue_type, labels_to_type_emoji, reactions_to_str


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
