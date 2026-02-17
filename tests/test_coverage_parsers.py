from app.utils.coverage_parsers import (
    extract_python_coverage_summary,
    parse_python_coverage_payload,
    parse_vitest_coverage_payload,
)


def test_parse_python_coverage_payload_and_summary() -> None:
    payload = {
        "files": {
            "lib/streamlit/foo.py": {"executed_lines": [1, 2, 3], "missing_lines": [4]},
            "lib/streamlit/bar.py": {"executed_lines": [10], "missing_lines": [11, 12, 13]},
        }
    }

    parsed = parse_python_coverage_payload(payload)
    assert parsed["lib/streamlit/foo.py"]["coverage_pct"] == 75.0
    assert parsed["lib/streamlit/bar.py"]["coverage_pct"] == 25.0

    summary = extract_python_coverage_summary(parsed)
    assert summary["total_stmts"] == 8
    assert summary["covered_stmts"] == 4
    assert summary["total_miss"] == 4
    assert summary["coverage_pct"] == 50.0


def test_parse_vitest_coverage_payload_removes_ci_prefix() -> None:
    payload = {
        "/home/runner/work/streamlit/streamlit/frontend/src/foo.ts": {
            "lines": {"total": 10, "covered": 8, "pct": 80},
            "functions": {"total": 5, "covered": 4, "pct": 80},
            "branches": {"total": 2, "covered": 1, "pct": 50},
        },
        "total": {
            "lines": {"total": 10, "covered": 8, "pct": 80},
            "functions": {"total": 5, "covered": 4, "pct": 80},
            "branches": {"total": 2, "covered": 1, "pct": 50},
            "statements": {"total": 10, "covered": 8, "pct": 80},
        },
    }

    parsed, totals = parse_vitest_coverage_payload(payload)
    assert "src/foo.ts" in parsed
    assert parsed["src/foo.ts"]["file_name"] == "foo.ts"
    assert totals["lines"]["pct"] == 80
