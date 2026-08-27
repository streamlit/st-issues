from datetime import date

from app.utils.ai_workflow_runs import _month_ranges, normalize_conclusion, trigger_label


def test_normalize_conclusion_maps_github_statuses() -> None:
    assert normalize_conclusion("success") == "Succeeded"
    assert normalize_conclusion("failure") == "Failed"
    assert normalize_conclusion("startup_failure") == "Failed"
    assert normalize_conclusion("timed_out") == "Failed"
    assert normalize_conclusion("cancelled") == "Cancelled"
    assert normalize_conclusion(None) == "In progress"
    assert normalize_conclusion("action_required") == "Action required"


def test_trigger_label_maps_known_events() -> None:
    assert trigger_label("pull_request") == "PR label"
    assert trigger_label("issues") == "Issue label"
    assert trigger_label("workflow_dispatch") == "Manual"
    assert trigger_label("schedule") == "Schedule"
    assert trigger_label(None) == "Unknown"


def test_month_ranges_are_newest_first_and_include_current_month() -> None:
    ranges = _month_ranges(3)
    assert len(ranges) == 3
    today = date.today()
    current_start, current_end = ranges[0]
    assert current_start == today.replace(day=1).isoformat()
    assert current_end >= today.isoformat()
    assert ranges[0][0] > ranges[1][0] > ranges[2][0]
