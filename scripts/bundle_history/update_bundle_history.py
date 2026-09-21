"""Append newly published releases to bundle_history.csv, measuring only those.

`collect_bundle_history.py` rebuilds the whole history, which means downloading
every wheel (~10 MB each, ~500 MB for the full span). This script is the
incremental form meant for CI: it diffs PyPI's stable releases against the rows
already in the CSV and measures only what is missing, so a scheduled run costs
one wheel download and a couple of seconds.

Exits 0 whether or not anything was added; the caller checks `added_count` (also
written to `$GITHUB_OUTPUT` when running under GitHub Actions) to decide whether
there is a commit to make.

Usage:
    uv run python update_bundle_history.py --history ../../static/bundle_history/bundle_history.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

from collect_bundle_history import (
    download_wheel,
    fetch_release_index,
    measure,
    version_key,
)

# How far back to look on PyPI for releases missing from the CSV. Only needs to
# exceed the number of releases published between two runs, with slack for a run
# that was skipped or failing for a while.
DEFAULT_LOOKBACK = 10


def read_existing(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Return the CSV's rows and its field order, or empty values if absent."""
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def emit_output(name: str, value: str) -> None:
    """Publish a step output when running under GitHub Actions."""
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with Path(output_path).open("a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, default=Path("bundle_history.csv"))
    parser.add_argument(
        "--lookback",
        type=int,
        default=DEFAULT_LOOKBACK,
        help="how many recent stable releases to check for gaps",
    )
    parser.add_argument("--cache-dir", type=Path, default=Path("wheel_cache"))
    args = parser.parse_args()

    existing, fieldnames = read_existing(args.history)
    known = {row["version"] for row in existing}
    if not existing:
        print(
            f"{args.history} has no rows; run collect_bundle_history.py to seed it first.",
            file=sys.stderr,
        )
        sys.exit(1)

    candidates = fetch_release_index(limit=args.lookback)
    missing = [release for release in candidates if release["version"] not in known]

    if not missing:
        print(
            f"Up to date: {len(existing)} releases, newest {max(known, key=version_key)}."
        )
        emit_output("added_count", "0")
        emit_output("added", "")
        return

    args.cache_dir.mkdir(parents=True, exist_ok=True)
    added = []
    for release in sorted(missing, key=lambda r: version_key(r["version"])):
        print(f"Measuring {release['version']}...", file=sys.stderr)
        wheel = download_wheel(release, args.cache_dir)
        added.append(measure(wheel, release))

    merged = existing + [
        {key: str(value) for key, value in row.items()} for row in added
    ]
    merged.sort(key=lambda row: version_key(row["version"]))

    with args.history.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames or list(added[0]))
        writer.writeheader()
        writer.writerows(merged)

    versions = [row["version"] for row in added]
    print(f"Added {len(added)} release(s) to {args.history}: {', '.join(versions)}")
    for row in added:
        print(
            f"  {row['version']:>8}  {row['released_at']}  "
            f"total={int(row['total_gzip']) / 1024 / 1024:6.2f} MiB  "
            f"initial={int(row['initial_gzip']) / 1024:7.1f} KiB"
        )

    emit_output("added_count", str(len(added)))
    emit_output("added", ", ".join(versions))


if __name__ == "__main__":
    main()
