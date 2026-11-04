"""Builders for Apache ECharts option dicts rendered with ``st.echarts_chart``.

Every builder takes a pandas dataframe and returns a plain option dict. Chart
data goes into ``dataset.source`` as a dataframe (sent to the browser as Arrow),
so the option dicts stay small and the hover toolbar can show the data table.
Callers can tweak the returned dict before passing it to ``st.echarts_chart``.
"""

from __future__ import annotations

import operator
from collections.abc import Mapping, Sequence
from typing import Any, Literal

import pandas as pd

AxisType = Literal["time", "category", "value", "log"]
SeriesKind = Literal["line", "bar", "scatter", "area"]
SelectMode = Literal["single", "multiple"]
Agg = Literal["sum", "mean", "median", "min", "max", "count", "first", "last"]

# A sequential blue scale used for treemaps and other single-hue encodings.
BLUES = ["#c6dbef", "#6baed6", "#2171b5", "#08306b"]
# Red-to-green scale for scores where higher is better (coverage, success rate).
RED_TO_GREEN = ["#d73027", "#fc8d59", "#fee08b", "#d9ef8b", "#91cf60", "#1a9850"]


def pivot_series(
    df: pd.DataFrame,
    *,
    x: str,
    y: str,
    color: str,
    agg: Agg = "sum",
    order: Sequence[str] | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Pivot long data into one column per ``color`` group.

    Returns the wide dataframe (``x`` as its first column) and the series column
    names in display order. Missing combinations become null, so lines can
    connect across them and stacked bars treat them as zero height.
    """
    if color == x:
        color = f"{x} (series)"
        df = df.assign(**{color: df[x]})
    wide = df.pivot_table(index=x, columns=color, values=y, aggfunc=agg, observed=True)
    wide.columns = [str(column) for column in wide.columns]
    series = [str(name) for name in order if str(name) in wide.columns] if order is not None else list(wide.columns)
    series += [column for column in wide.columns if column not in series]
    wide = wide[series].reset_index()
    return wide, series


def item_tooltip(dims: Sequence[str], *, labels: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Build a series ``tooltip`` listing each dataset dimension as ``label: value``.

    Values are inserted as raw text without number formatting, so pass
    pre-formatted string columns for numbers or dates that need it.
    """
    rows = [f"{(labels or {}).get(dim, dim)}: <b>{{@{dim}}}</b>" for dim in dims]
    return {"trigger": "item", "formatter": "{a}<br/>" + "<br/>".join(rows)}


def _axis(
    axis_type: AxisType,
    *,
    title: str | None = None,
    label_format: str | None = None,
    minimum: float | str | None = None,
    maximum: float | str | None = None,
    inverse: bool = False,
    title_location: Literal["end", "middle"] = "end",
) -> dict[str, Any]:
    axis: dict[str, Any] = {"type": axis_type}
    if axis_type in {"value", "log"}:
        axis["scale"] = minimum is None
    if title:
        axis["name"] = title
        axis["nameLocation"] = title_location
        if title_location == "middle":
            axis["nameGap"] = 32
    if label_format:
        axis["axisLabel"] = {"formatter": label_format}
    if minimum is not None:
        axis["min"] = minimum
    if maximum is not None:
        axis["max"] = maximum
    if inverse:
        axis["inverse"] = True
    return axis


def _base_option(*, title: str | None, legend: bool, subtitle: str | None = None) -> dict[str, Any]:
    option: dict[str, Any] = {}
    if title:
        option["title"] = {"text": title, "left": 0}
        if subtitle:
            option["title"]["subtext"] = subtitle
    if legend:
        option["legend"] = {"type": "scroll", "top": 32 if title else 0, "right": 0 if title else "center"}
        if title:
            option["legend"]["left"] = "center"
    if title or legend:
        option["grid"] = {"top": 72 if title and legend else 48}
    return option


def cartesian_chart(
    df: pd.DataFrame,
    *,
    x: str,
    y: str | Sequence[str],
    color: str | None = None,
    kind: SeriesKind = "line",
    x_type: AxisType = "time",
    horizontal: bool = False,
    stack: bool = False,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
    value_format: str | None = None,
    axis_label_format: str | None = None,
    y_min: float | None = None,
    y_max: float | None = None,
    log_scale: bool = False,
    symbols: bool | None = None,
    smooth: bool = False,
    zoom: bool = False,
    select: SelectMode | None = None,
    agg: Agg = "sum",
    color_order: Sequence[str] | None = None,
    series_names: Mapping[str, str] | None = None,
    legend: bool | None = None,
    tooltip_dims: Sequence[str] | None = None,
    mark_lines: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a line, area, bar, or scatter chart from a dataframe.

    Args:
        df: Source data in long format (with ``color``) or wide format (with a
            list of ``y`` columns).
        x: Column for the category or time dimension. For horizontal bars, this
            is still the category column; it's drawn on the vertical axis.
        y: Value column, or several value columns drawn as separate series.
        color: Column whose values split ``y`` into one series each. The data is
            pivoted, so ``x``/``color`` duplicates are aggregated with ``agg``.
        kind: Series type. ``"area"`` is a filled line.
        x_type: Axis type for ``x``.
        horizontal: Draw bars horizontally (category axis on the left).
        stack: Stack the series on top of each other.
        title: Chart title drawn inside the chart.
        x_title: Name of the category or time axis.
        y_title: Name of the value axis.
        value_format: Streamlit number format for tooltip values
            (``"%.1f%%"``, ``"compact"``, ``"bytes"``, ...).
        axis_label_format: ECharts string template for value axis labels, for
            example ``"{value}%"``.
        y_min: Lower bound of the value axis. Bars start at zero by default.
        y_max: Upper bound of the value axis.
        log_scale: Use a logarithmic value axis.
        symbols: Show point symbols on lines. Defaults to on for lines and off
            for areas.
        smooth: Draw smoothed lines.
        zoom: Add an inside and a slider ``dataZoom`` on the category axis.
        select: Enable point selection on every series (needs
            ``on_select`` on ``st.echarts_chart``).
        agg: Aggregation for duplicate ``x``/``color`` pairs when pivoting.
        color_order: Series order for ``color`` groups; unlisted groups follow.
        series_names: Display names for value columns, keyed by column name.
        legend: Show the legend. Defaults to on with more than one series.
        tooltip_dims: Extra columns listed in an item tooltip next to the value
            (see ``item_tooltip``).
        mark_lines: ECharts ``markLine.data`` entries added to the first series,
            such as ``{"yAxis": 80, "name": "Target"}``.
    """
    y_columns = [y] if isinstance(y, str) else list(y)
    if color is not None:
        if len(y_columns) != 1:
            message = "`color` requires a single `y` column."
            raise ValueError(message)
        source, series_columns = pivot_series(df, x=x, y=y_columns[0], color=color, agg=agg, order=color_order)
    else:
        source = df.reset_index(drop=True)
        series_columns = y_columns

    show_legend = legend if legend is not None else len(series_columns) > 1
    option = _base_option(title=title, legend=show_legend)
    option["dataset"] = {"source": source}

    trigger = "item" if kind == "scatter" or tooltip_dims else "axis"
    tooltip: dict[str, Any] = {"trigger": trigger}
    if value_format:
        tooltip["valueFormatter"] = value_format
    option["tooltip"] = tooltip

    category_axis = _axis(x_type, title=x_title, inverse=horizontal and x_type == "category")
    value_axis = _axis(
        "log" if log_scale else "value",
        title=y_title,
        label_format=axis_label_format,
        minimum=y_min,
        maximum=y_max,
    )
    if kind == "bar" and y_min is None and not log_scale:
        value_axis["scale"] = False
    if horizontal:
        option["xAxis"], option["yAxis"] = value_axis, category_axis
    else:
        option["xAxis"], option["yAxis"] = category_axis, value_axis

    if zoom:
        zoom_axis = {"yAxisIndex": 0} if horizontal else {"xAxisIndex": 0}
        option["dataZoom"] = [{"type": "inside", **zoom_axis}, {"type": "slider", **zoom_axis}]
        option.setdefault("grid", {})["bottom"] = 64
        if show_legend:
            option["legend"]["top"] = option["legend"].get("top", 0)

    series_list: list[dict[str, Any]] = []
    for column in series_columns:
        encode: dict[str, Any] = {"x": column, "y": x} if horizontal else {"x": x, "y": column}
        if tooltip_dims:
            encode["tooltip"] = [column, *tooltip_dims]
        series: dict[str, Any] = {
            "type": "line" if kind == "area" else kind,
            "name": (series_names or {}).get(column, column),
            "encode": encode,
        }
        if tooltip_dims:
            series["tooltip"] = item_tooltip([column, *tooltip_dims], labels={column: y_title or column})
        if kind in {"line", "area"}:
            series["connectNulls"] = True
            series["showSymbol"] = symbols if symbols is not None else kind == "line"
            if smooth:
                series["smooth"] = True
        if kind == "area":
            series["areaStyle"] = {}
        if kind == "bar" and len(series_columns) > 1 and not stack:
            series["barGap"] = "10%"
        if stack:
            series["stack"] = "total"
            if kind == "bar":
                series["emphasis"] = {"focus": "series"}
        if select:
            series["selectedMode"] = select
        series_list.append(series)

    if mark_lines and series_list:
        series_list[0]["markLine"] = {
            "symbol": "none",
            "lineStyle": {"type": "dashed"},
            "label": {"formatter": "{b}", "position": "insideEndTop"},
            "data": list(mark_lines),
        }
    option["series"] = series_list
    return option


def pie_chart(
    df: pd.DataFrame,
    *,
    names: str,
    values: str,
    title: str | None = None,
    donut: bool = True,
    value_format: str | None = None,
    label: str = "{b}: {d}%",
    colors: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Build a pie or donut chart with one slice per row."""
    option = _base_option(title=title, legend=False)
    option.pop("grid", None)
    option["dataset"] = {"source": df[[names, values]].reset_index(drop=True)}
    tooltip: dict[str, Any] = {"trigger": "item"}
    if value_format:
        tooltip["valueFormatter"] = value_format
    option["tooltip"] = tooltip
    series: dict[str, Any] = {
        "type": "pie",
        "radius": ["40%", "70%"] if donut else "70%",
        "center": ["50%", "55%" if title else "50%"],
        "encode": {"itemName": names, "value": values},
        "label": {"formatter": label},
        "itemStyle": {"borderColor": "transparent", "borderWidth": 2},
    }
    option["series"] = [series]
    if colors:
        option["color"] = list(colors)
    return option


def boxplot_stats(df: pd.DataFrame, *, group: str, value: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute Tukey box plot statistics per group.

    Returns the per-group stats (``group``, ``low``, ``q1``, ``median``, ``q3``,
    ``high``, ``count``) and the outlier rows (``group`` and ``value``) that fall
    beyond 1.5 times the interquartile range.
    """
    rows: list[dict[str, Any]] = []
    outliers: list[pd.DataFrame] = []
    for name, values in df.groupby(group, sort=False, observed=True)[value]:
        clean = values.dropna()
        if clean.empty:
            continue
        q1, median, q3 = clean.quantile([0.25, 0.5, 0.75])
        fence = 1.5 * (q3 - q1)
        inside = clean[(clean >= q1 - fence) & (clean <= q3 + fence)]
        rows.append(
            {
                group: name,
                "low": inside.min(),
                "q1": q1,
                "median": median,
                "q3": q3,
                "high": inside.max(),
                "count": len(clean),
            }
        )
        outside = clean[(clean < q1 - fence) | (clean > q3 + fence)]
        if not outside.empty:
            outliers.append(pd.DataFrame({group: name, value: outside.to_numpy()}))
    stats = pd.DataFrame(rows, columns=[group, "low", "q1", "median", "q3", "high", "count"])
    outlier_df = pd.concat(outliers, ignore_index=True) if outliers else pd.DataFrame(columns=[group, value])
    return stats, outlier_df


def boxplot_chart(
    df: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str | None = None,
    y_title: str | None = None,
    value_format: str | None = None,
    order: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Build a box plot of ``y`` per ``x`` category, with outliers as points."""
    stats, outliers = boxplot_stats(df, group=x, value=y)
    if order is not None:
        rank = {name: index for index, name in enumerate(order)}
        stats = stats.sort_values(x, key=lambda column: column.map(rank)).reset_index(drop=True)
    stats[x] = stats[x].astype(str)
    outliers[x] = outliers[x].astype(str)

    option = _base_option(title=title, legend=False)
    tooltip: dict[str, Any] = {"trigger": "item"}
    if value_format:
        tooltip["valueFormatter"] = value_format
    option["tooltip"] = tooltip
    option["dataset"] = [{"source": stats}, {"source": outliers}]
    option["xAxis"] = {"type": "category", "data": stats[x].tolist()}
    option["yAxis"] = _axis("value", title=y_title)
    option["series"] = [
        {
            "type": "boxplot",
            "name": y_title or y,
            "datasetIndex": 0,
            "encode": {"x": x, "y": ["low", "q1", "median", "q3", "high"], "tooltip": ["median", "q1", "q3", "count"]},
        },
        {
            "type": "scatter",
            "name": "Outliers",
            "datasetIndex": 1,
            "encode": {"x": x, "y": y},
            "symbolSize": 6,
        },
    ]
    return option


def treemap_data(df: pd.DataFrame, *, path: Sequence[str], value: str) -> list[dict[str, Any]]:
    """Nest rows into ECharts treemap nodes along the ``path`` columns."""

    def build(frame: pd.DataFrame, depth: int) -> list[dict[str, Any]]:
        column = path[depth]
        nodes: list[dict[str, Any]] = []
        for name, group in frame.groupby(column, sort=False, observed=True):
            node: dict[str, Any] = {"name": str(name), "value": float(group[value].sum())}
            if depth + 1 < len(path):
                node["children"] = build(group, depth + 1)
            nodes.append(node)
        return sorted(nodes, key=operator.itemgetter("value"), reverse=True)

    return build(df, 0)


def treemap_chart(
    nodes: list[dict[str, Any]],
    *,
    name: str,
    value_format: str | None = None,
    color_range: Sequence[str] | None = None,
    color_min: float | None = None,
    color_max: float | None = None,
    color_dimension: int = 0,
) -> dict[str, Any]:
    """Build a treemap from nested ``{"name", "value", "children"}`` nodes.

    Set ``color_range`` to color leaves by ``value[color_dimension]`` (for
    example a coverage percentage stored as ``value: [size, percent]``).
    """
    tooltip: dict[str, Any] = {"trigger": "item"}
    if value_format:
        tooltip["valueFormatter"] = value_format
    series: dict[str, Any] = {
        "type": "treemap",
        "name": name,
        "data": nodes,
        "roam": False,
        "nodeClick": "zoomToNode",
        "leafDepth": 2,
        "breadcrumb": {"show": True, "bottom": 0},
        "label": {"show": True, "formatter": "{b}"},
        "upperLabel": {"show": True, "height": 22},
        "itemStyle": {"borderColor": "transparent", "gapWidth": 2},
    }
    levels: list[dict[str, Any]] = [
        {"itemStyle": {"gapWidth": 4}, "upperLabel": {"show": False}},
        {"itemStyle": {"gapWidth": 2}},
        {"itemStyle": {"gapWidth": 1}},
    ]
    series["levels"] = levels
    option: dict[str, Any] = {"tooltip": tooltip, "series": [series]}
    if color_range:
        leaf_values = [_color_value(leaf["value"], color_dimension) for leaf in _leaves(nodes)]
        series["visualDimension"] = color_dimension
        series["visualMin"] = color_min if color_min is not None else min(leaf_values, default=0)
        series["visualMax"] = color_max if color_max is not None else max(leaf_values, default=1)
        series["color"] = list(color_range)
        series["colorMappingBy"] = "value"
        levels[-1]["color"] = list(color_range)
        levels[-1]["colorMappingBy"] = "value"
    return option


def _leaves(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    leaves: list[dict[str, Any]] = []
    for node in nodes:
        children = node.get("children")
        leaves.extend(_leaves(children) if children else [node])
    return leaves


def _color_value(value: Any, dimension: int) -> float:
    if isinstance(value, list | tuple):
        return float(value[dimension])
    return float(value)


def gauge_chart(
    value: float,
    *,
    title: str,
    minimum: float = 0,
    maximum: float = 100,
    unit: str = "%",
    bands: Sequence[tuple[float, str]] = ((0.5, "#d73027"), (0.8, "#f5a623"), (1.0, "#1a9850")),
) -> dict[str, Any]:
    """Build a single-value gauge.

    ``bands`` are ``(fraction_of_range, color)`` pairs, sorted by fraction. The
    progress bar takes the color of the first band that contains the value.
    """
    fraction = (value - minimum) / (maximum - minimum) if maximum > minimum else 0
    color = next((band_color for limit, band_color in bands if fraction <= limit), bands[-1][1])
    return {
        "series": [
            {
                "type": "gauge",
                "min": minimum,
                "max": maximum,
                "progress": {"show": True, "width": 14, "itemStyle": {"color": color}},
                "axisLine": {"lineStyle": {"width": 14}},
                "pointer": {"show": False},
                "axisTick": {"show": False},
                "splitLine": {"show": False},
                "axisLabel": {"show": False},
                "anchor": {"show": False},
                "title": {"offsetCenter": [0, "30%"], "fontSize": 14},
                "detail": {"valueAnimation": True, "offsetCenter": [0, "-5%"], "formatter": f"{{value}}{unit}"},
                "data": [{"value": round(float(value), 2), "name": title}],
            }
        ]
    }


def selected_rows(event: Any, *, series_index: int | None = None) -> list[int]:
    """Return the selected dataset row indices from an ``st.echarts_chart`` event.

    Pass ``series_index`` to only read the selection of one series (for example,
    the scatter series of a combined chart).
    """
    selection = getattr(event, "selection", None) or {}
    groups = selection.get("selected", []) if isinstance(selection, Mapping) else []
    rows: list[int] = []
    for group in groups:
        if series_index is not None and group.get("series_index") != series_index:
            continue
        for index in group.get("data_indices", []):
            if index not in rows:
                rows.append(index)
    return rows
