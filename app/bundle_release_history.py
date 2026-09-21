"""Frontend bundle size per published release, measured from PyPI wheels.

The per-commit sections above this one read `bundle_analysis_json` artifacts from
`pr-preview.yml`, showing the most recent successful develop runs - about a week
at the default run limit, roughly three at the maximum. Published wheels never
expire and ship the real built frontend under `streamlit/static/`, so measuring
them gives a history bounded only by PyPI: the same question, coarser zoom, much
longer reach.

The two are never plotted on one axis: the analyzer sums *per-module* gzip sizes,
which overstates a chunk by ~6% on Total and ~27% on Entry against real gzip of
the emitted files. See the methodology note at the bottom of the page.

Data is precomputed by `scripts/bundle_history/` into `static/bundle_history/`.
"""

from __future__ import annotations

from pathlib import Path

import altair as alt
import humanize
import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent.parent / "static" / "bundle_history"

# Categorical slots 1-3, validated for CVD separation on both surfaces. Slot 2
# (Entry) has no metric tile: out of context that number reads backwards, so it
# appears only as a chart beside Initial load.
LIGHT_HUES = ["#2a78d6", "#eb6834", "#1baf7a"]
DARK_HUES = ["#3987e5", "#d95926", "#199e70"]

KIB = 1024
MIB = 1024 * 1024

# The entry chunk stops tracking the initial load here: from this release the
# initial load is code-split, so the entry chunk is an arbitrary fraction of it.
ENTRY_SPLIT_FROM = (1, 56, 0)

METRICS = [
    (
        "Total (gzip)",
        "total_gzip",
        "Every file under `streamlit/static/` gzipped: the whole shipped frontend, including lazily loaded chunks most sessions never fetch.",
    ),
    (
        "Initial load (gzip)",
        "initial_gzip",
        "Entry chunk plus every chunk and stylesheet it statically imports: what the browser must download before first render. The metric to judge releases on.",
    ),
]


def is_dark() -> bool:
    theme = getattr(st.context, "theme", None)
    return getattr(theme, "type", "light") == "dark"


def hues() -> list[str]:
    """Return series colors stepped for the viewer's active theme."""
    return DARK_HUES if is_dark() else LIGHT_HUES


def format_bytes(size: float | None) -> str:
    if size is None or pd.isna(size):
        return "N/A"
    return humanize.naturalsize(size, binary=True)


def format_delta(delta: float) -> str:
    sign = "+" if delta > 0 else "-" if delta < 0 else ""
    return f"{sign}{format_bytes(abs(delta))}"


def version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


@st.cache_data(show_spinner=False)
def load_history() -> pd.DataFrame:
    history = pd.read_csv(DATA_DIR / "bundle_history.csv")
    history["released_at"] = pd.to_datetime(history["released_at"])
    # Sort by release order, not date: patch releases can ship out of date
    # order, and the ordinal x-axis and pct_change both assume release order.
    history["vkey"] = history["version"].apply(version_key)
    history = history.sort_values("vkey").reset_index(drop=True)
    history["entry_split"] = history["vkey"] >= ENTRY_SPLIT_FROM
    return history.drop(columns="vkey")


def release_rule_layer(since: pd.Timestamp, until: pd.Timestamp) -> alt.Chart | None:
    """Dashed rules at each release inside a per-commit chart's date range.

    Lets a commit-level move be read against the release that shipped it. Returns
    None when no release falls in the window - releases ship every two weeks or
    so, and the per-commit window is often shorter than that.
    """
    history = load_history()

    # The per-commit data is tz-aware (GitHub timestamps); release dates are not.
    left, right = (pd.Timestamp(value) for value in (since, until))
    if left.tzinfo is not None:
        left = left.tz_localize(None)
    if right.tzinfo is not None:
        right = right.tz_localize(None)

    in_window = history[history["released_at"].between(left, right)]
    if in_window.empty:
        return None

    base = alt.Chart(in_window[["version", "released_at"]])
    rule = base.mark_rule(color="#8a8a86", strokeDash=[4, 3], strokeWidth=1).encode(  # ty: ignore[unresolved-attribute]
        x=alt.X("released_at:T"),
        tooltip=[alt.Tooltip("version:N", title="Released")],
    )
    label = base.mark_text(align="left", baseline="top", dx=3, dy=2, fontSize=10, color="#8a8a86").encode(  # ty: ignore[unresolved-attribute]
        x=alt.X("released_at:T"),
        text="version:N",
    )
    return rule + label


def trend_chart(view: pd.DataFrame, column: str, title: str, unit: str, color: str) -> alt.Chart:
    """Single-series release trend. One measure per chart - never a second y-axis."""
    divisor = MIB if unit == "MiB" else KIB
    data = view.assign(display=view[column] / divisor, pretty=view[column].apply(format_bytes))
    return (
        alt.Chart(data)
        .mark_line(point=alt.OverlayMarkDef(size=60, filled=True), strokeWidth=2, color=color)
        .encode(  # ty: ignore[unresolved-attribute]
            x=alt.X(
                "version:N",
                title=None,
                sort=view["version"].tolist(),
                axis=alt.Axis(labelAngle=-45),
            ),
            y=alt.Y(
                "display:Q",
                title=f"Size ({unit})",
                scale=alt.Scale(zero=False, nice=True),
                axis=alt.Axis(grid=True, gridDash=[], tickCount=5),
            ),
            tooltip=[
                alt.Tooltip("version:N", title="Release"),
                alt.Tooltip("released_at:T", title="Date", format="%b %d, %Y"),
                alt.Tooltip("pretty:N", title=title),
            ],
        )
        .properties(title=title, height=280)
    )


def split_marker(view: pd.DataFrame) -> alt.Chart | None:
    """Rule at the release where the entry chunk stopped tracking the initial load."""
    split = view[view["entry_split"]]
    if split.empty or split.index[0] == 0:
        return None
    return (
        alt.Chart(pd.DataFrame({"version": [split["version"].iloc[0]]}))
        .mark_rule(color="#8a8a86", strokeDash=[4, 3], strokeWidth=1)
        .encode(x=alt.X("version:N", sort=view["version"].tolist()))  # ty: ignore[unresolved-attribute]
    )


def render_headline_metrics(view: pd.DataFrame) -> None:
    latest, baseline = view.iloc[-1], view.iloc[0]
    # Release-over-release, because that is the change someone can still act on;
    # the sparkline already shows the shape of the whole window.
    previous = view.iloc[-2] if len(view) > 1 else None

    for column, (label, key, help_text) in zip(st.columns(len(METRICS)), METRICS, strict=True):
        if previous is None:
            delta = None
            note = ""
        else:
            step = latest[key] - previous[key]
            step_pct = step / previous[key] * 100 if previous[key] else float("nan")
            delta = f"{format_delta(step)} ({step_pct:+.1f}%)"
            window_pct = (latest[key] / baseline[key] - 1) * 100 if baseline[key] else float("nan")
            note = (
                f"\n\nDelta is vs. the previous release ({previous['version']}). "
                f"Across the {len(view)} releases shown: {window_pct:+.1f}% since {baseline['version']}."
            )

        column.metric(
            f"{label} vs. last release" if previous is not None else label,
            format_bytes(latest[key]),
            delta=delta,
            delta_color="inverse",
            help=f"{help_text}{note}",
            border=True,
            chart_data=view[key],
            chart_type="line",
        )


def render_trends(view: pd.DataFrame) -> None:
    palette = hues()

    st.altair_chart(
        trend_chart(view, "total_gzip", "Total (gzip)", "MiB", palette[0]),
        width="stretch",
    )

    left, right = st.columns(2)
    with left:
        st.altair_chart(
            trend_chart(view, "initial_gzip", "Initial load (gzip)", "KiB", palette[2]),
            width="stretch",
        )
        st.caption(
            ":material/check_circle: **What users download before first render** - the entry chunk plus everything it "
            "statically imports. Comparable across the whole window, including the webpack → Vite migration."
        )
    with right:
        entry_chart = trend_chart(view, "entry_gzip", "Entry (gzip)", "KiB", palette[1])
        marker = split_marker(view)
        st.altair_chart(entry_chart + marker if marker is not None else entry_chart, width="stretch")
        if marker is not None:
            st.caption(
                f":material/warning: **The entry chunk alone.** Dashed line marks "
                f"{view[view['entry_split']]['version'].iloc[0]}, where the initial load became code-split: left of it "
                "the entry chunk *is* essentially the initial load, right of it the two measure different things."
            )


def render_release_table(view: pd.DataFrame) -> None:
    st.subheader("Release detail")

    table = view.iloc[::-1].copy()
    for key in ("total_gzip", "initial_gzip", "entry_gzip"):
        table[f"{key}_pct"] = view[key].pct_change().reindex(table.index)
        table[f"{key}_fmt"] = table[key].apply(format_bytes)
    table["wheel_fmt"] = table["wheel_bytes"].apply(format_bytes)
    table["notes"] = table["js_file_count"].astype(str) + " JS chunks"

    st.dataframe(
        table[
            [
                "version",
                "released_at",
                "total_gzip_fmt",
                "total_gzip_pct",
                "initial_gzip_fmt",
                "initial_gzip_pct",
                "entry_gzip_fmt",
                "entry_gzip_pct",
                "wheel_fmt",
                "notes",
            ]
        ],
        column_config={
            "version": st.column_config.TextColumn("Release"),
            "released_at": st.column_config.DatetimeColumn("Date", format="MMM DD, YYYY"),
            "total_gzip_fmt": st.column_config.TextColumn("Total (gzip)"),
            "total_gzip_pct": st.column_config.NumberColumn(
                "Δ Total",
                format="percent",
                help="Change vs. the previous release shown.",
            ),
            "initial_gzip_fmt": st.column_config.TextColumn("Initial load (gzip)"),
            "initial_gzip_pct": st.column_config.NumberColumn(
                "Δ Initial",
                format="percent",
                help="Change vs. the previous release shown.",
            ),
            "entry_gzip_fmt": st.column_config.TextColumn("Entry (gzip)"),
            "entry_gzip_pct": st.column_config.NumberColumn(
                "Δ Entry",
                format="percent",
                help="Change vs. the previous release shown.",
            ),
            "wheel_fmt": st.column_config.TextColumn(
                "Wheel",
                help="Size of the published wheel. The per-commit wheel trend lives on the Wheel size page.",
            ),
            "notes": st.column_config.TextColumn("Chunking"),
        },
        hide_index=True,
        width="stretch",
    )


def render_methodology() -> None:
    with st.expander("Methodology - release sizes vs per-commit sizes"):
        st.markdown(
            """
            **Two sources, one page.** The release sections measure the built frontend inside each published wheel
            (`streamlit/static/`), so their history is bounded only by PyPI. The per-commit sections read
            `bundle_analysis_json` artifacts from `pr-preview.yml`. Their window is set by the run limit in the sidebar,
            not by retention: 50 runs is roughly a week of develop commits and 250 is roughly three weeks, while the
            artifacts themselves last 90 days. That is why this release history exists - it is the only view here that
            can see past a few weeks.

            **Why the absolute values differ, and why they are never plotted together.** The bundle analyzer reports a
            chunk's `gzipSize` as the *sum of its modules' individual gzip sizes*, which throws away redundancy shared
            across modules. The release figures are real gzip of each emitted file at level 6 (Node's zlib default, and
            what CDNs typically serve). Both are internally consistent, so trends agree; only the analyzer's absolute
            figures overstate what users actually download. The overstatement is typically around -27% on the entry
            chunk and -6% on the total. Both are internally consistent, so **trends** computed within each source agree;
            only the absolute figures differ. Never compare a release-section number directly to a per-commit-section
            number.

            **Initial load is release-only for now.** Computing it needs the static import graph, which lives in the
            Vite manifest. The build already emits `manifest.json`, but `pr-preview.yml` does not upload it, so the
            per-commit sections cannot show initial load. Walking the analyzer's own `imports` is not a substitute: it
            mixes static and dynamic imports and reaches 367 items / 6.5 MB from the entry.

            **Three build systems.** The measured span crosses two tooling boundaries, and the rule for finding the
            entry point differs in each:

            | Releases | Build | Entry and initial load resolved from |
            | --- | --- | --- |
            | 1.33.0 - 1.40.2 | webpack / CRA | `asset-manifest.json`; its `entrypoints` *is* the initial load |
            | 1.41.0 - 1.45.1 | Vite, no manifest | `index.html` script tag, then a scan of static ESM imports |
            | 1.46.0 - | Vite + manifest | `manifest.json`: the `isEntry` node and its `imports` closure |

            The ESM-scan rule was validated against manifest ground truth on ten later releases that have both, and
            agreed exactly, which is what licenses using it for the releases that have no manifest. Sourcemaps are
            excluded throughout - 1.41.0 ships 70 of them and no user downloads them.

            **Staying current.** A scheduled workflow checks PyPI daily for stable releases missing from
            `static/bundle_history/bundle_history.csv`, measures each one, and opens a pull request with the new rows.
            One release costs a 10 MB wheel download and about 3 seconds, so it needs no changes to the release
            process. The CSV is append-only: new releases are added and older rows are never dropped, so the
            history grows from the initial seed (today: 1.33.0) onward.
            """
        )


def render() -> None:
    """Render the per-release sections at the bottom of the bundle analysis page."""
    history = load_history()

    st.subheader("Bundle size trends — by release")

    st.sidebar.header("Releases")
    window = st.sidebar.slider(
        "Releases to show",
        min_value=5,
        max_value=len(history),
        value=len(history),
        help="Trims the release sections to the most recent N releases.",
    )
    view = history.tail(window).reset_index(drop=True)

    st.caption(
        f"Covering {len(history)} stable releases ({history['version'].iloc[0]} → {history['version'].iloc[-1]}), "
        "measured from the built frontend inside each published PyPI wheel."
    )

    render_headline_metrics(view)

    eras = view["era"].nunique()
    if eras > 1:
        st.caption(
            f"Spans {eras} build systems ({', '.join(view['era'].unique())}). Sizes stay comparable; emitted chunk "
            "names do not."
        )

    render_trends(view)
    render_release_table(view)
    render_methodology()
