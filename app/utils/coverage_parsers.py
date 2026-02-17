from __future__ import annotations

import pathlib
from typing import Any


def parse_python_coverage_payload(coverage_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Parse a coverage.py JSON payload into a normalized file mapping."""
    coverage_info: dict[str, dict[str, Any]] = {}

    for file_path, file_data in coverage_payload["files"].items():
        file_name = pathlib.Path(file_path).name
        executed_lines = file_data.get("executed_lines", [])
        missing_lines = file_data.get("missing_lines", [])
        total_lines = len(executed_lines) + len(missing_lines)
        coverage_pct = (len(executed_lines) / total_lines * 100) if total_lines > 0 else 0

        coverage_info[file_path] = {
            "file_name": file_name,
            "file_path": file_path,
            "executed_lines": executed_lines,
            "missing_lines": missing_lines,
            "total_lines": total_lines,
            "coverage_pct": coverage_pct,
        }

    return coverage_info


def extract_python_coverage_summary(coverage_data: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Extract overall summary statistics from parsed coverage.py data."""
    total_lines = 0
    total_covered = 0
    total_files = len(coverage_data)

    for file_info in coverage_data.values():
        total_lines += file_info["total_lines"]
        total_covered += len(file_info["executed_lines"])

    coverage = (total_covered / total_lines) if total_lines > 0 else 0
    return {
        "total_files": total_files,
        "total_stmts": total_lines,
        "covered_stmts": total_covered,
        "total_miss": total_lines - total_covered,
        "coverage": coverage,
        "coverage_pct": coverage * 100,
    }


def parse_vitest_coverage_payload(
    coverage_payload: dict[str, Any],
    *,
    path_prefix_to_remove: str = "/home/runner/work/streamlit/streamlit/frontend/",
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Parse Vitest JSON summary payload into normalized file stats plus totals."""
    coverage_info: dict[str, dict[str, Any]] = {}

    for file_path, file_data in coverage_payload.items():
        if file_path == "total":
            continue

        clean_path = file_path.removeprefix(path_prefix_to_remove)
        file_name = pathlib.Path(clean_path).name

        coverage_info[clean_path] = {
            "file_name": file_name,
            "file_path": clean_path,
            "lines_total": file_data["lines"]["total"],
            "lines_covered": file_data["lines"]["covered"],
            "lines_pct": file_data["lines"]["pct"],
            "functions_total": file_data["functions"]["total"],
            "functions_covered": file_data["functions"]["covered"],
            "functions_pct": file_data["functions"]["pct"],
            "branches_total": file_data["branches"]["total"],
            "branches_covered": file_data["branches"]["covered"],
            "branches_pct": file_data["branches"]["pct"],
        }

    return coverage_info, coverage_payload.get("total", {})
