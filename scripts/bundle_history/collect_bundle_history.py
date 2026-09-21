"""Build a frontend bundle-size history from published Streamlit wheels.

The dashboard at issues.streamlit.app/frontend_bundle_analysis reads
`bundle_analysis_json` artifacts from the `pr-preview.yml` workflow. Those
artifacts expire, which is why its trend only reaches back a few weeks. Released
wheels never expire and ship the real built frontend under `streamlit/static/`,
so they give us a per-release history as far back as we like.

Sizes here are measured by actually compressing each emitted file, so they are
download bytes. This differs from the analyzer's `gzipSize`, which sums
*per-module* gzip sizes within a chunk and therefore overstates large chunks
(~37% on the entry chunk) because it loses cross-module redundancy.

Retention policy
----------------
The CSV is **append-only**: once a release row is present it is never removed.
The page shows every row in the file. New releases are added by
``update_bundle_history.py`` (CI) or by re-running this script.

``--since-days`` is only a cold-seed helper: on an empty (or missing) output
file it limits how far back on PyPI to measure. It does not prune existing
rows. Re-running against an existing CSV merges newly measured releases and
keeps everything already collected.

``--releases`` is an optional hard cap for ad-hoc sampling.

Usage:
    # Cold seed: measure recent stables (default window: last 730 days)
    uv run python collect_bundle_history.py --out bundle_history.csv

    # Ad-hoc: measure only the 5 most recent releases
    uv run python collect_bundle_history.py --releases 5 --out bundle_history.csv
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import sys
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path, PurePosixPath

PYPI_JSON = "https://pypi.org/pypi/streamlit/json"
STATIC_PREFIX = "streamlit/static/"
STABLE_VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

# Node's zlib default (Z_DEFAULT_COMPRESSION) is 6, and CDNs typically serve
# gzip at 6 as well, so it is the most representative single level to report.
GZIP_LEVEL = 6

JS_SUFFIXES = (".js", ".mjs", ".cjs")
CSS_SUFFIXES = (".css",)

# Sourcemaps ship in 1.41.0 only. They are never downloaded during a page load,
# so counting them would put a spike in the total that no user experiences.
EXCLUDED_SUFFIXES = (".map",)

STATIC_SCRIPT_SRC = re.compile(r'<script[^>]*\ssrc=["\']([^"\']+)')
# Static ESM forms: `import x from "y"`, bare `import "y"`, `export * from "y"`.
# Deliberately excludes `import("y")` — dynamic chunks are not part of first paint.
STATIC_IMPORT = re.compile(
    r"""(?:\bimport\s*(?:[\w${}*\s,]*?\s*from\s*)?|\bexport\s*(?:\*|\{[^}]*\})\s*from\s*)["']([^"']+)["']"""
)


def version_key(version: str) -> tuple[int, int, int]:
    major, minor, patch = STABLE_VERSION.match(version).groups()
    return int(major), int(minor), int(patch)


def fetch_release_index(
    limit: int | None = None,
    since_days: int | None = None,
) -> list[dict]:
    """Return metadata for stable Streamlit releases, newest first.

    Parameters
    ----------
    limit:
        Hard cap on the number of releases returned. When *None*, all
        qualifying releases are returned.  Pass a small number (e.g. 10) from
        the incremental updater to look back only at the most recent releases.
    since_days:
        When set, restrict to releases whose upload date is within the last
        *since_days* calendar days (inclusive).  ``None`` means no date filter.
    """
    with urllib.request.urlopen(PYPI_JSON) as response:
        releases = json.load(response)["releases"]

    cutoff = (date.today() - timedelta(days=since_days)).isoformat() if since_days is not None else None

    stable = []
    for version, files in releases.items():
        if not STABLE_VERSION.match(version):
            continue
        wheels = [f for f in files if f["filename"].endswith(".whl") and not f.get("yanked")]
        if not wheels:
            continue
        wheel = wheels[0]
        released_at = wheel["upload_time_iso_8601"][:10]
        if cutoff is not None and released_at < cutoff:
            continue
        stable.append(
            {
                "version": version,
                "released_at": released_at,
                "wheel_url": wheel["url"],
                "wheel_bytes": wheel["size"],
            }
        )

    stable.sort(key=lambda r: version_key(r["version"]), reverse=True)
    if limit is not None:
        stable = stable[:limit]
    return stable


def download_wheel(release: dict, cache_dir: Path) -> Path:
    path = cache_dir / f"streamlit-{release['version']}.whl"
    if path.exists() and path.stat().st_size == release["wheel_bytes"]:
        return path
    print(f"  downloading {release['version']}...", file=sys.stderr)
    with urllib.request.urlopen(release["wheel_url"]) as response:  # ruff: ignore[suspicious-url-open-usage]
        data = response.read()
    path.write_bytes(data)
    return path


def resolve_via_manifest(manifest: dict) -> tuple[str, set[str]]:
    """Vite with a manifest: walk the `imports` graph from the entry node."""
    entry_file = next(v["file"] for v in manifest.values() if v.get("isEntry"))

    files: set[str] = set()
    seen: set[str] = set()
    queue = [k for k, v in manifest.items() if v.get("isEntry")]
    while queue:
        key = queue.pop()
        if key in seen or key not in manifest:
            continue
        seen.add(key)
        node = manifest[key]
        if node.get("file"):
            files.add(node["file"])
        # `css` lists stylesheets the chunk needs, which also block first render.
        files.update(node.get("css", []))
        queue.extend(node.get("imports", []))
    return entry_file, files


def resolve_via_asset_manifest(asset_manifest: dict) -> tuple[str, set[str]]:
    """Webpack/CRA: `entrypoints` *is* the initial load (a main .js plus its .css).

    Note the asymmetry in these files: `files` values carry a `./` prefix while
    `entrypoints` values do not, so strip it unconditionally.
    """
    files = {f.lstrip("./") for f in asset_manifest["entrypoints"]}
    entry_file = next(f for f in files if f.endswith(JS_SUFFIXES))
    return entry_file, files


def resolve_via_import_scan(archive: zipfile.ZipFile, names: set[str], html: str) -> tuple[str, set[str]]:
    """Vite before manifests were emitted: follow static ESM imports from the entry.

    Only *static* specifiers count toward first paint — `import("x")` is a lazy
    chunk, and the trailing paren is what distinguishes it from `import "x"`.
    Verified byte-identical to the manifest closure on ten later releases that
    have both, which is what licenses using it for the releases that don't.
    """
    entry_file = STATIC_SCRIPT_SRC.search(html).group(1).lstrip("./")

    js: set[str] = set()
    seen: set[str] = set()
    queue = [entry_file]
    while queue:
        current = queue.pop()
        if current in seen or current not in names:
            continue
        seen.add(current)
        if current.endswith(JS_SUFFIXES):
            js.add(current)
        text = archive.read(STATIC_PREFIX + current).decode("utf-8", "replace")
        parent = str(PurePosixPath(current).parent)
        for specifier in STATIC_IMPORT.findall(text):
            if specifier.startswith((".", "/")):
                target = normalize_specifier(parent, specifier)
                if target in names:
                    queue.append(target)

    css = {
        match.group(1).lstrip("./")
        for tag in re.findall(r"<link[^>]*>", html)
        if "stylesheet" in tag
        for match in [re.search(r'href=["\']([^"\']+)', tag)]
        if match
    }
    return entry_file, js | css


def normalize_specifier(base: str, specifier: str) -> str:
    """Resolve a relative ESM specifier against the importing chunk's directory."""
    parts: list[str] = []
    for part in f"{base}/{specifier}".split("/"):
        if part == "..":
            if parts:
                parts.pop()
        elif part not in {".", ""}:
            parts.append(part)
    return "/".join(parts)


def resolve_assets(archive: zipfile.ZipFile, names: set[str]) -> tuple[str, str, set[str]]:
    """Return (era, entry file, initial-load files) for whichever build produced this wheel.

    Three eras appear across the releases measured here: webpack/CRA through
    1.40.2, Vite without a manifest through 1.45.1, and Vite with one from 1.46.0.
    """
    html = archive.read(STATIC_PREFIX + "index.html").decode("utf-8", "replace")

    if "asset-manifest.json" in names:
        entry, files = resolve_via_asset_manifest(json.loads(archive.read(STATIC_PREFIX + "asset-manifest.json")))
        return "webpack", entry, files

    if "manifest.json" in names:
        entry, files = resolve_via_manifest(json.loads(archive.read(STATIC_PREFIX + "manifest.json")))
        return "vite+manifest", entry, files

    entry, files = resolve_via_import_scan(archive, names, html)
    return "vite-scan", entry, files


def categorize(name: str) -> str:
    lowered = name.lower()
    if lowered.endswith(JS_SUFFIXES):
        return "js"
    if lowered.endswith(CSS_SUFFIXES):
        return "css"
    if lowered.endswith(".html"):
        return "html"
    return "other"


def measure(wheel_path: Path, release: dict) -> dict:
    archive = zipfile.ZipFile(wheel_path)
    names = {n[len(STATIC_PREFIX) :] for n in archive.namelist() if n.startswith(STATIC_PREFIX) and not n.endswith("/")}

    era, entry_file, initial_files = resolve_assets(archive, names)

    row = {
        "version": release["version"],
        "released_at": release["released_at"],
        "era": era,
        "wheel_bytes": release["wheel_bytes"],
        "total_gzip": 0,
        "total_raw": 0,
        "entry_gzip": 0,
        "entry_raw": 0,
        "initial_gzip": 0,
        "initial_raw": 0,
        "js_gzip": 0,
        "css_gzip": 0,
        "other_gzip": 0,
        "file_count": 0,
        "js_file_count": 0,
        "initial_file_count": 0,
        "initial_js_count": 0,
    }

    for relative in names:
        if relative.endswith(EXCLUDED_SUFFIXES):
            continue
        raw = archive.read(STATIC_PREFIX + relative)
        compressed = len(gzip.compress(raw, compresslevel=GZIP_LEVEL, mtime=0))

        row["total_raw"] += len(raw)
        row["total_gzip"] += compressed
        row["file_count"] += 1

        category = categorize(relative)
        if category == "js":
            row["js_gzip"] += compressed
            row["js_file_count"] += 1
        elif category == "css":
            row["css_gzip"] += compressed
        elif category == "other":
            row["other_gzip"] += compressed

        if relative == entry_file:
            row["entry_gzip"] += compressed
            row["entry_raw"] += len(raw)
        if relative in initial_files:
            row["initial_gzip"] += compressed
            row["initial_raw"] += len(raw)
            row["initial_file_count"] += 1
            if category == "js":
                row["initial_js_count"] += 1

    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--since-days",
        type=int,
        default=730,
        metavar="DAYS",
        help=(
            "cold-seed helper: when measuring from PyPI, only consider stables "
            "from the last DAYS days (default: 730). Does not prune existing CSV rows."
        ),
    )
    parser.add_argument(
        "--releases",
        type=int,
        default=None,
        metavar="N",
        help="hard cap: fetch at most N releases (default: unlimited)",
    )
    parser.add_argument("--out", type=Path, default=Path("bundle_history.csv"))
    parser.add_argument("--cache-dir", type=Path, default=Path("wheel_cache"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    args.cache_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"Fetching stable releases from the last {args.since_days} days from PyPI...",
        file=sys.stderr,
    )
    releases = fetch_release_index(limit=args.releases, since_days=args.since_days)
    if not releases:
        print("No releases found matching the criteria.", file=sys.stderr)
        sys.exit(0)
    print(f"  {releases[-1]['version']} .. {releases[0]['version']} ({len(releases)} releases)", file=sys.stderr)

    # Merge into any existing CSV: never drop older rows already collected.
    existing_rows: list[dict] = []
    existing_fieldnames: list[str] = []
    if args.out.exists():
        with args.out.open(newline="") as handle:
            reader = csv.DictReader(handle)
            existing_rows = list(reader)
            existing_fieldnames = list(reader.fieldnames or [])

    known_versions = {row["version"] for row in existing_rows}
    to_measure = [r for r in releases if r["version"] not in known_versions]

    if not to_measure:
        print("All releases already present in the output file; nothing to do.", file=sys.stderr)
        sys.exit(0)

    print(f"  {len(to_measure)} release(s) not yet in {args.out}; measuring...", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        paths = list(pool.map(lambda r: download_wheel(r, args.cache_dir), to_measure))

    new_rows = []
    for release, path in zip(to_measure, paths, strict=True):
        print(f"  measuring {release['version']}...", file=sys.stderr)
        new_rows.append(measure(path, release))

    all_rows = existing_rows + new_rows
    all_rows.sort(key=lambda r: version_key(r["version"]))

    fieldnames = existing_fieldnames or list(all_rows[0])

    with args.out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nWrote {len(all_rows)} releases to {args.out} ({len(new_rows)} new)", file=sys.stderr)
    for row in new_rows:
        print(
            f"  {row['version']:>8}  {row['released_at']}  "
            f"total={int(row['total_gzip']) / 1024 / 1024:6.2f} MiB  "
            f"entry={int(row['entry_gzip']) / 1024:7.1f} KiB  "
            f"initial={int(row['initial_gzip']) / 1024:7.1f} KiB",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
